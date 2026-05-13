import logging
from typing import List, TypedDict
from dependencies import ConnectLLM, load_prompt, get_checkpointer
from userrepo import save_section
from langgraph.types import interrupt
from langchain.messages import SystemMessage, HumanMessage
from langgraph.graph import START, END, StateGraph, MessagesState

logger = logging.getLogger(__name__)  # GET LOGGER

llm = ConnectLLM()


class ProfessionalSummaryState(MessagesState):
    session_id: str
    user_input_initial: str
    refinement_counts: int
    generated_questions: List[str]
    user_answers: dict[str, str]
    refinements: List[str]
    # WILL CONTAIN ALL THREE DRAFT VERSIONS IN SEQUENCE. LAST DRAFT WILL BE THE FINAL DRAFT
    drafts: List[str]
    approved: bool
    current_stage: str


class GeneratedQuestionsResult(TypedDict):
    questions: List[str]


professional_summary_graph = StateGraph(ProfessionalSummaryState)

# THIS GRAPH GETS INVOKED BY UI WITH USER INPUT
# PREPAGE QUESTIONS TAKES THAT INPUT AND CALLS LLM AND PRESENTS USER WITH 5/10 QUESTIONS FOR REFINEMENT 1st ROUND
# GRAPH SHOULD PAUSE FOR USER INPUTS


def PSG_PrepareQuestions(state: ProfessionalSummaryState):
    system_prompt = load_prompt("prompts\PSG\prepare_questions.txt")
    llm_messages = [
        SystemMessage(system_prompt),
        HumanMessage(state["user_input_initial"])
    ]
    result = llm.with_structured_output(
        GeneratedQuestionsResult).invoke(llm_messages)
    logging.info(f"PSG_PrepareQuestions result {result}")

    return {
        # "messages": [result], # TEST AND ENSURE THIS IS PROPERLY HANDLED
        "generated_questions": result["questions"],
        "current_stage": "awaiting_answers"
    }


def PSG_CollectAnswers(state: ProfessionalSummaryState):
    user_answers = interrupt({
        # this gets returned to your UI
        "questions": state["generated_questions"]
    })
    return {"user_answers": user_answers}


def PSG_PrepareForIntialDraft(state: ProfessionalSummaryState):
    system_prompt = load_prompt("prompts\PSG\initial_draft.txt")
    qa_pairs = "\n".join(
        f"Q: {q}\nA: {state['user_answers'].get(q, 'No answer')}"
        for q in state["generated_questions"]
    )

    context = f"""
    User Background:
    {state["user_input_initial"]}
    Questions and Answers:
    {qa_pairs}
    """

    llm_messages = [
        SystemMessage(system_prompt),
        HumanMessage(context)
    ]
    result = llm.invoke(llm_messages)

    logging.info(f"PSG_PrepareForIntialDraft result {result}")
    return {
        "drafts": state.get("drafts", []) + [result.content],
        "current_stage": "pending_review"
    }

def PSG_PresentForReview(state: ProfessionalSummaryState):
    approved = interrupt({
        # this gets returned to your UI
        "drafts": state["drafts"],
        "questions":"Review the Draft and provide approval"
    })
    return {"approved":approved["approved"]}

def PSG_NeedRefinement(state:ProfessionalSummaryState):
    if state["approved"]:
        return "store"
    elif state.get("refinement_counts", 0) < 2:
        return "refine"
    else:
        return "store"

def PSG_AskInputs(state: ProfessionalSummaryState):
    refinement = interrupt({
        "refinement_question": "What would you like to refine in the summary?"
    })
    existing = state.get("refinements") or []
    return {
        "refinements": existing + [refinement["refinement"]],
        "refinement_counts": state.get("refinement_counts", 0) + 1,
        "current_stage":"refinement"
    }

def PSG_PrepareRefinedDraft(state: ProfessionalSummaryState):
    system_prompt = load_prompt("prompts\PSG\/refine_draft.txt")

    context = f"""
    Original Background:
    {state["user_input_initial"]}

    Current Draft:
    {state["drafts"][-1]}

    User Refinement Request:
    {state["refinements"][-1]}
    """

    logging.info(f"Refinement request: {state['refinements'][-1]}")
    logging.info(f"Current draft: {state['drafts'][-1]}")

    result = llm.invoke([SystemMessage(system_prompt), HumanMessage(context)])

    logging.info(f"Refined draft: {result.content}")

    return {
        "drafts": state.get("drafts", []) + [result.content],
        "current_stage": "pending_refinement_review"
    }

def PSG_StoreDB(state:ProfessionalSummaryState):
    save_section(state['session_id'],"summary",state["drafts"][-1])
    return {"current_stage":"Completed"}

def build_psg_graph():
    # NODES
    professional_summary_graph.add_node("PSG_PrepareQuestions",PSG_PrepareQuestions)
    professional_summary_graph.add_node("PSG_CollectAnswers",PSG_CollectAnswers)
    professional_summary_graph.add_node("PSG_PrepareForIntialDraft",PSG_PrepareForIntialDraft)
    professional_summary_graph.add_node("PSG_PresentForReview",PSG_PresentForReview)
    professional_summary_graph.add_node("PSG_AskInputs",PSG_AskInputs)
    professional_summary_graph.add_node("PSG_StoreDB",PSG_StoreDB)
    professional_summary_graph.add_node("PSG_PrepareRefinedDraft",PSG_PrepareRefinedDraft)
    

    # EDGES
    professional_summary_graph.add_edge(START,"PSG_PrepareQuestions")
    professional_summary_graph.add_edge("PSG_PrepareQuestions","PSG_CollectAnswers")
    professional_summary_graph.add_edge("PSG_CollectAnswers","PSG_PrepareForIntialDraft")
    professional_summary_graph.add_edge("PSG_PrepareForIntialDraft","PSG_PresentForReview")

    professional_summary_graph.add_edge("PSG_AskInputs","PSG_PrepareRefinedDraft")
    professional_summary_graph.add_edge("PSG_PrepareRefinedDraft","PSG_PresentForReview")

    professional_summary_graph.add_edge("PSG_StoreDB",END)
    
    # professional_summary_graph.add_edge("PSG_PrepareForIntialDraft",END)

    professional_summary_graph.add_conditional_edges("PSG_PresentForReview",PSG_NeedRefinement,{
        "refine": "PSG_AskInputs",
        "store": "PSG_StoreDB"
    })

def PSG_GRAPH():
    build_psg_graph()
    return professional_summary_graph.compile(checkpointer=get_checkpointer())