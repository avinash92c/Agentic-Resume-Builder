import logging
import json
import copy
import time
from typing import List, Optional
from typing_extensions import TypedDict

from pydantic import BaseModel
from dependencies import ConnectLLM, load_prompt, get_checkpointer
from userrepo import save_section
from langgraph.types import interrupt
from langchain.messages import SystemMessage, HumanMessage
from langgraph.graph import START, END, StateGraph, MessagesState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LLM initialisation — lazy so a cold-start failure doesn't crash the module.
# ---------------------------------------------------------------------------

_llm = None

def get_llm():
    """
    Return a cached LLM client, initialising on first call.
    Raises LLMUnavailableError with a human-readable message if the
    service cannot be reached so callers can surface it to the UI.
    """
    global _llm
    if _llm is None:
        try:
            _llm = ConnectLLM()
            logger.info("LLM client initialised successfully.")
        except Exception as exc:
            logger.error(f"LLM initialisation failed: {exc}", exc_info=True)
            raise LLMUnavailableError(
                "The AI service could not be started. "
                "Please check your API key and network connection."
            ) from exc
    return _llm


# ---------------------------------------------------------------------------
# Custom exceptions — caught at node level and converted to UI-visible errors
# ---------------------------------------------------------------------------

class LLMUnavailableError(RuntimeError):
    """Raised when the LLM client cannot be initialised or reached."""

class LLMInvocationError(RuntimeError):
    """Raised when an LLM call fails after all retries."""

class PromptLoadError(RuntimeError):
    """Raised when a prompt file cannot be loaded."""


# ---------------------------------------------------------------------------
# Retry helper
# ---------------------------------------------------------------------------

_LLM_MAX_RETRIES   = 3
_LLM_RETRY_BACKOFF = 2   # seconds; doubles each attempt (exponential)

def invoke_llm_with_retry(llm_call, *args, node_name: str = "unknown", **kwargs):
    """
    Call `llm_call(*args, **kwargs)` up to _LLM_MAX_RETRIES times.

    On each failure logs the attempt, waits with exponential back-off,
    then re-raises as LLMInvocationError after all retries are exhausted.
    """
    last_exc = None
    for attempt in range(1, _LLM_MAX_RETRIES + 1):
        try:
            result = llm_call(*args, **kwargs)
            if attempt > 1:
                logger.info(f"[{node_name}] LLM call succeeded on attempt {attempt}.")
            return result
        except Exception as exc:
            last_exc = exc
            wait = _LLM_RETRY_BACKOFF ** (attempt - 1)
            logger.warning(
                f"[{node_name}] LLM call attempt {attempt}/{_LLM_MAX_RETRIES} failed "
                f"({type(exc).__name__}: {exc}). "
                f"{'Retrying in ' + str(wait) + 's...' if attempt < _LLM_MAX_RETRIES else 'No more retries.'}"
            )
            if attempt < _LLM_MAX_RETRIES:
                time.sleep(wait)

    raise LLMInvocationError(
        f"[{node_name}] LLM call failed after {_LLM_MAX_RETRIES} attempts. "
        f"Last error: {type(last_exc).__name__}: {last_exc}"
    ) from last_exc


def load_prompt_safe(path: str, node_name: str = "unknown") -> str:
    """Load a prompt file; raise PromptLoadError on any IO failure."""
    try:
        return load_prompt(path)
    except Exception as exc:
        logger.error(f"[{node_name}] Failed to load prompt '{path}': {exc}", exc_info=True)
        raise PromptLoadError(
            f"[{node_name}] Could not load prompt file '{path}': {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class WorkExperience(TypedDict):
    company_name: str
    job_title: str
    start_date: str
    end_date: str
    employment_type: str
    projects: List[str]

class Project(TypedDict):
    company: str
    project: str

class WorkHistoryState(MessagesState):
    session_id: str
    user_input_initial: List[WorkExperience]
    pending_projects: List[Project]
    current_project_index: int
    refinement_counts: int
    generated_questions: List[str]
    user_answers: dict[str, str]
    refinements: List[str]
    drafts: List[str]
    approved: bool
    current_stage: str
    # ── Error propagation ──────────────────────────────────────────────────
    # When a node catches a fatal error it writes here instead of crashing.
    # The API layer reads this field and returns a structured 200 with
    # error details so the frontend can display a meaningful message.
    error: Optional[str]

class GeneratedQuestionsResult(TypedDict):
    questions: List[str]


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

work_history_graph = StateGraph(WorkHistoryState)


def WH_FlattenProjects(state: WorkHistoryState):
    flattened = []
    for company in state["user_input_initial"]:
        company_name = company["company_name"]
        for project_data in company["projects"]:
            flattened.append(Project(company=company_name, project=project_data))
    return {
        "pending_projects": flattened,
        "current_project_index": 0,
        "drafts": [],
        "error": None,
        "current_stage": "flattened_projects",
    }


def WH_SelectProject(state: WorkHistoryState):
    current_index = state.get("current_project_index", 0)
    return {
        "current_project_index": current_index,
        "current_stage": "select_project",
    }


def WH_PrepareQuestions(state: WorkHistoryState):
    node = "WH_PrepareQuestions"
    try:
        system_prompt = load_prompt_safe(r"prompts\WH\prepare_questions.txt", node)
        selected_project = state["pending_projects"][state["current_project_index"]]

        llm = get_llm()
        result = invoke_llm_with_retry(
            llm.with_structured_output(GeneratedQuestionsResult).invoke,
            [SystemMessage(system_prompt), HumanMessage(json.dumps(selected_project))],
            node_name=node,
        )
        logger.info(f"[{node}] result: {result}")
        return {
            "generated_questions": result["questions"],
            "current_stage": "awaiting_answers",
            "error": None,
        }

    except (LLMUnavailableError, LLMInvocationError, PromptLoadError) as exc:
        logger.error(f"[{node}] {exc}", exc_info=True)
        return {
            "error": str(exc),
            "current_stage": "error",
        }


def WH_CollectAnswers(state: WorkHistoryState):
    # Propagate upstream errors without blocking on interrupt
    if state.get("error"):
        return {}

    user_answers = interrupt({"questions": state["generated_questions"]})
    return {
        "user_answers": user_answers,
        "current_stage": "ready_for_project_draft",
    }


def WH_PrepareDraft(state: WorkHistoryState):
    node = "WH_PrepareDraft"
    if state.get("error"):
        return {}

    try:
        system_prompt = load_prompt_safe(r"prompts\WH\initial_project_draft.txt", node)
        selected_index = state["current_project_index"]
        selected_project = state["pending_projects"][selected_index]
        qa_pairs = "\n".join(
            f"Q: {q}\nA: {state['user_answers'].get(q, 'No answer')}"
            for q in state["generated_questions"]
        )
        context = f"User Work History:\n{selected_project}\n\nQuestions and Answers:\n{qa_pairs}"

        llm = get_llm()
        result = invoke_llm_with_retry(
            llm.invoke,
            [SystemMessage(system_prompt), HumanMessage(context)],
            node_name=node,
        )
        logger.info(f"[{node}] result: {result}")

        pending_projects = state["pending_projects"].copy()
        pending_projects[selected_index]["project"] = result.content
        return {
            "pending_projects": pending_projects,
            "current_stage": "select_next_project",
            "current_project_index": selected_index + 1,
            "error": None,
        }

    except (LLMUnavailableError, LLMInvocationError, PromptLoadError) as exc:
        logger.error(f"[{node}] {exc}", exc_info=True)
        return {
            "error": str(exc),
            "current_stage": "error",
        }


def WH_HasMoreProjects(state: WorkHistoryState):
    # Route errors straight to a terminal error node instead of looping
    if state.get("error"):
        return "error"
    if state["current_project_index"] < len(state["pending_projects"]):
        return "next_project"
    return "review"


def WH_PrepareOverallDraft(state: WorkHistoryState):
    node = "WH_PrepareOverallDraft"
    if state.get("error"):
        return {}

    try:
        system_prompt = load_prompt_safe(r"prompts\WH\overall_draft.txt", node)
        pending_projects = state["pending_projects"]
        overall_input = copy.deepcopy(state["user_input_initial"])

        project_company_drafts: dict[str, List[str]] = {}
        for record in pending_projects:
            project_company_drafts.setdefault(record["company"], []).append(record["project"])

        for company in overall_input:
            company["projects"] = project_company_drafts[company["company_name"]]

        raw_input_llm = json.dumps(overall_input)
        logger.info(f"[{node}] input: {raw_input_llm}")

        llm = get_llm()
        result = invoke_llm_with_retry(
            llm.invoke,
            [SystemMessage(system_prompt), HumanMessage(raw_input_llm)],
            node_name=node,
        )
        logger.info(f"[{node}] initial overall draft: {result.content}")
        return {
            "user_input_initial": overall_input,
            "drafts": [result.content],
            "current_stage": "ready_for_review",
            "error": None,
        }

    except (LLMUnavailableError, LLMInvocationError, PromptLoadError) as exc:
        logger.error(f"[{node}] {exc}", exc_info=True)
        return {
            "error": str(exc),
            "current_stage": "error",
        }


def WH_PresentForReview(state: WorkHistoryState):
    if state.get("error"):
        return {}

    draft = state["drafts"][-1]
    approved = interrupt({
        "drafts": draft,
        "approval_question": "Review the Draft and provide approval",
    })
    return {
        "approved": approved["approved"],
        "current_stage": "awaiting_approval",
    }


def WH_AskInputsForRefinement(state: WorkHistoryState):
    refinement = interrupt({
        "refinement_question": "What would you like to refine in the summary?"
    })
    existing = state.get("refinements") or []
    return {
        "refinements": existing + [refinement["refinement"]],
        "refinement_counts": state.get("refinement_counts", 0) + 1,
        "current_stage": "refinement",
    }


def WH_PrepareRefinementDraft(state: WorkHistoryState):
    node = "WH_PrepareRefinementDraft"
    if state.get("error"):
        return {}

    try:
        system_prompt = load_prompt_safe(r"prompts\WH\refine_draft.txt", node)
        context = (
            f"Original Background:\n{json.dumps(state['user_input_initial'])}\n\n"
            f"Current Draft:\n{state['drafts'][-1]}\n\n"
            f"User Refinement Request:\n{state['refinements'][-1]}"
        )
        logger.info(f"[{node}] refinement request: {state['refinements'][-1]}")
        logger.info(f"[{node}] current draft: {state['drafts'][-1]}")

        llm = get_llm()
        result = invoke_llm_with_retry(
            llm.invoke,
            [SystemMessage(system_prompt), HumanMessage(context)],
            node_name=node,
        )
        logger.info(f"[{node}] refined draft: {result.content}")
        return {
            "drafts": state.get("drafts", []) + [result.content],
            "current_stage": "pending_refinement_review",
            "error": None,
        }

    except (LLMUnavailableError, LLMInvocationError, PromptLoadError) as exc:
        logger.error(f"[{node}] {exc}", exc_info=True)
        return {
            "error": str(exc),
            "current_stage": "error",
        }


def WH_NeedRefinement(state: WorkHistoryState):
    if state.get("error"):
        return "store"  # error path — WH_StoreDB will skip and surface the error
    if state["approved"]:
        return "store"
    elif state.get("refinement_counts", 0) <= 2:   # fixed: <= 2 allows 2 refinements
        return "refine"
    else:
        return "store"


def WH_ErrorNode(state: WorkHistoryState):
    """
    Terminal error node — interrupts the graph so the API layer can return
    a structured error payload to the frontend instead of a raw 500.
    """
    error_message = state.get("error", "An unexpected error occurred.")
    logger.error(f"[WH_ErrorNode] Graph halted: {error_message}")
    # interrupt() surfaces the error payload back through the same
    # resume mechanism the UI already uses — the API layer checks for
    # the 'error' key and returns it as a 4xx/5xx with a message field.
    interrupt({"error": error_message})
    return {}


def WH_StoreDB(state: WorkHistoryState):
    node = "WH_StoreDB"
    # If an error reached this node via the NeedRefinement "store" fallback,
    # do not write corrupt/empty data — surface the error instead.
    if state.get("error"):
        logger.error(f"[{node}] Skipping DB write due to upstream error: {state['error']}")
        return {"current_stage": "error"}

    try:
        save_section(state["session_id"], "work_history", state["drafts"][-1])
        logger.info(f"[{node}] Work history saved for session {state['session_id']}")
        return {"current_stage": "completed"}
    except Exception as exc:
        logger.error(f"[{node}] DB save failed: {exc}", exc_info=True)
        return {
            "error": f"Your draft was generated but could not be saved: {exc}",
            "current_stage": "error",
        }


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_wh_graph():
    work_history_graph.add_node("WH_FlattenProjects",         WH_FlattenProjects)
    work_history_graph.add_node("WH_SelectProject",           WH_SelectProject)
    work_history_graph.add_node("WH_PrepareQuestions",        WH_PrepareQuestions)
    work_history_graph.add_node("WH_CollectAnswers",          WH_CollectAnswers)
    work_history_graph.add_node("WH_PrepareDraft",            WH_PrepareDraft)
    work_history_graph.add_node("WH_PrepareOverallDraft",     WH_PrepareOverallDraft)
    work_history_graph.add_node("WH_PresentForReview",        WH_PresentForReview)
    work_history_graph.add_node("WH_AskInputsForRefinement",  WH_AskInputsForRefinement)
    work_history_graph.add_node("WH_PrepareRefinementDraft",  WH_PrepareRefinementDraft)
    work_history_graph.add_node("WH_StoreDB",                 WH_StoreDB)
    work_history_graph.add_node("WH_ErrorNode",               WH_ErrorNode)

    # Main flow
    work_history_graph.add_edge(START,                        "WH_FlattenProjects")
    work_history_graph.add_edge("WH_FlattenProjects",         "WH_SelectProject")
    work_history_graph.add_edge("WH_SelectProject",           "WH_PrepareQuestions")
    work_history_graph.add_edge("WH_PrepareQuestions",        "WH_CollectAnswers")
    work_history_graph.add_edge("WH_CollectAnswers",          "WH_PrepareDraft")

    work_history_graph.add_conditional_edges("WH_PrepareDraft", WH_HasMoreProjects, {
        "next_project": "WH_SelectProject",
        "review":       "WH_PrepareOverallDraft",
        "error":        "WH_ErrorNode",       # new error route
    })

    work_history_graph.add_edge("WH_PrepareOverallDraft",     "WH_PresentForReview")

    work_history_graph.add_conditional_edges("WH_PresentForReview", WH_NeedRefinement, {
        "refine": "WH_AskInputsForRefinement",
        "store":  "WH_StoreDB",
    })

    work_history_graph.add_edge("WH_AskInputsForRefinement",  "WH_PrepareRefinementDraft")
    work_history_graph.add_edge("WH_PrepareRefinementDraft",  "WH_PresentForReview")
    work_history_graph.add_edge("WH_StoreDB",                 END)
    work_history_graph.add_edge("WH_ErrorNode",               END)


def WH_GRAPH():
    build_wh_graph()
    return work_history_graph.compile(checkpointer=get_checkpointer())