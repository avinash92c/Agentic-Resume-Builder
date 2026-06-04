import logging
import json
import copy
from typing import List #, TypedDict
from typing_extensions import TypedDict

from pydantic import BaseModel
from dependencies import ConnectLLM, load_prompt, get_checkpointer
from userrepo import save_section
from langgraph.types import interrupt
from langchain.messages import SystemMessage, HumanMessage
from langgraph.graph import START, END, StateGraph, MessagesState

logger = logging.getLogger(__name__)  # GET LOGGER

llm = ConnectLLM()

class WorkExperience(TypedDict):
    company_name: str
    job_title: str
    start_date: str
    end_date: str                    # or "Present"
    employment_type: str             # full time, contract etc
    # location: str                    # or remote
    projects: List[str]              # raw project descriptions

class Project(TypedDict):
    company:str
    project:str
    # project_refined:str

class WorkHistoryState(MessagesState):
    session_id: str
    user_input_initial: List[WorkExperience] # COMPANY,PROJECT WISE DETAILS
    pending_projects: List[Project]                  # projects not yet questioned
    current_project_index: int                         # project being processed now
    refinement_counts: int
    generated_questions: List[str] # PROJECT WISE QUESTIONS
    user_answers: dict[str, str] # PROJECT WISE QUESTION AND ANSWERS
    refinements: List[str] # REFINEMENTS
    # WILL CONTAIN ALL THREE DRAFT VERSIONS IN SEQUENCE. LAST DRAFT WILL BE THE FINAL DRAFT
    drafts: List[str] #REFINED DRAFTS
    approved: bool
    current_stage: str

class GeneratedQuestionsResult(TypedDict):
    # questions: dict[str, List[str]]
    questions: List[str]

work_history_graph = StateGraph(WorkHistoryState)

def WH_FlattenProjects(state:WorkHistoryState):
    # flattened = [
    #     item
    #     for sublist in state["user_input_initial"].values()
    #     for item in sublist
    # ]

    flattened = []

    for company in state["user_input_initial"]:
        company_name = company["company_name"]
        for project_data in company["projects"]:
            flattened.append(Project(company=company_name, project=project_data))
    
    return {
        "pending_projects": flattened,
        "current_project_index": 0,
        "drafts": [],
        "current_stage": "flattened_projects"
    }

def WH_SelectProject(state:WorkHistoryState):
    # PICKS ONE PROJECT AT A TIME AND ASKS CURATED QUESTIONS
    current_index = state.get("current_project_index", 0)
    return{
        "current_project_index":current_index,
        "current_stage": "select_project"
    }

def WH_PrepareQuestions(state:WorkHistoryState):
    # TAKES INPUT WORK HISTORY AND HAS LLM ASK 5 QUESTIONS PER PROJECT TO FURTHER ENHANCE
    system_prompt = load_prompt("prompts\WH\prepare_questions.txt")
    selected_index = state["current_project_index"]
    selected_project = state["pending_projects"][selected_index]
    llm_messages = [
        SystemMessage(system_prompt),
        HumanMessage(json.dumps(selected_project))
    ]
    result = llm.with_structured_output(GeneratedQuestionsResult).invoke(llm_messages)
    logging.info(f"WH_PrepareQuestions result {result}")

    return {
        # "messages": [result], # TEST AND ENSURE THIS IS PROPERLY HANDLED
        "generated_questions": result["questions"],
        "current_stage": "awaiting_answers"
    }

def WH_CollectAnswers(state:WorkHistoryState):
    # TAKES ASKED QUESTION AND ANSWERS AND PASSES TO LLM TO GENERATE DRAFT
    user_answers = interrupt({
        # this gets returned to your UI
        "questions": state["generated_questions"]
    })
    return {
        "user_answers": user_answers,
        "current_stage": "ready_for_project_draft"
    }

def WH_PrepareDraft(state:WorkHistoryState):
    # ASK LLM TO PREPARE A DRAFT
    system_prompt = load_prompt("prompts\WH\initial_project_draft.txt")
    qa_pairs = "\n".join(
        f"Q: {q}\nA: {state['user_answers'].get(q, 'No answer')}"
        for q in state["generated_questions"]
    )
    selected_index = state["current_project_index"]
    selected_project = state["pending_projects"][selected_index]

    context = f"""
    User Work History:
    {selected_project}
    Questions and Answers:
    {qa_pairs}
    """

    llm_messages = [
        SystemMessage(system_prompt),
        HumanMessage(context)
    ]
    result = llm.invoke(llm_messages)

    logging.info(f"WH_PrepareDraft result {result}")

    # state["pending_projects"][selected_index] = result.content
    pending_projects = state["pending_projects"].copy()
    pending_projects[selected_index]["project"] = result.content

    return {
        # "drafts": state.get("drafts", []) + [result.content],
        "pending_projects":pending_projects,
        "current_stage": "select_next_project",
        "current_project_index":selected_index+1
    }

def WH_HasMoreProjects(state:WorkHistoryState):
    if state["current_project_index"]<len(state["pending_projects"]):
        return "next_project"
    else:
        return "review"
    
def WH_PrepareOverallDraft(state:WorkHistoryState):
    system_prompt = load_prompt("prompts\WH\overall_draft.txt")

    pending_projects = state["pending_projects"]
    overall_input = copy.deepcopy(state["user_input_initial"])

    # REPLACE LIST OF PROJECTS IN USER_INPUT_INITIAL WITH PENDING_PROJECTS LIST
    # LLM REFINED THE DATA FOR THE PROJECTS SO PUSH THEM INTO OVERALL DATA AND USE THAT TO GENERATE FULL DRAFT
    
    # MAKE PENDING PROJECTS INTO A DICT FOR QUICK REFERENCE
    project_company_drafts : dict[str,List[str]] = {}
    for record in pending_projects:
        if record["company"] not in project_company_drafts:
            project_company_drafts[record["company"]] = []
        
        project_company_drafts[record['company']].append(record["project"])

    for company in overall_input:
        company["projects"] = project_company_drafts[company["company_name"]]

    raw_input_llm = json.dumps(overall_input)

    logging.info(f"WH_PrepareOverallDraft {raw_input_llm}")

    messages = [
        SystemMessage(system_prompt),
        HumanMessage(raw_input_llm)
    ]

    result = llm.invoke(messages)

    logging.info(f"Initial Overall draft: {result.content}")

    return {
        "user_input_initial" : overall_input,
        "drafts":[result.content],
        "current_stage": "ready_for_review"
    }

def WH_PresentForReview(state:WorkHistoryState):
    # ASK USER TO REVIEW
    # FLATTEN PROJECTS INTO SINGLE DRAFT
    # projects = "\n\n".join(state["pending_projects"])

    draft = state["drafts"][-1]
    
    approved = interrupt({
        # this gets returned to your UI
        # "drafts": state["drafts"][-1],
        "drafts":draft,
        "approval_question":"Review the Draft and provide approval"
    })
    return {
        # "drafts":[draft],
        "approved":approved["approved"],
        "current_stage": "awaiting_approval"
    }

def WH_AskInputsForRefinement(state:WorkHistoryState):
    # ASK USER Input Refinements
    refinement = interrupt({
        "refinement_question": "What would you like to refine in the summary?"
    })
    existing = state.get("refinements") or []
    return {
        "refinements": existing + [refinement["refinement"]],
        "refinement_counts": state.get("refinement_counts", 0) + 1,
        "current_stage":"refinement"
    }

def WH_PrepareRefinementDraft(state:WorkHistoryState):
    # ASK LLM TO PREPARE ANOTHER DRAFT BASED ON REFINEMENTS
    system_prompt = load_prompt("prompts\WH\/refine_draft.txt")

    user_input_initial = json.dumps(state["user_input_initial"])

    context = f"""
    Original Background:
    {user_input_initial}

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

def WH_NeedRefinement(state:WorkHistoryState):
    if state["approved"]:
        return "store"
    elif state.get("refinement_counts", 0) < 2:
        return "refine"
    else:
        return "store"

def WH_StoreDB(state:WorkHistoryState):
    # STORE APPROVED DRAFT TO DB
    save_section(state['session_id'],"work_history",state["drafts"][-1])
    return {"current_stage":"completed"}

def build_wh_graph():
    work_history_graph.add_node("WH_FlattenProjects",WH_FlattenProjects)
    work_history_graph.add_node("WH_SelectProject",WH_SelectProject)
    work_history_graph.add_node("WH_PrepareQuestions",WH_PrepareQuestions)
    work_history_graph.add_node("WH_CollectAnswers",WH_CollectAnswers)
    work_history_graph.add_node("WH_PrepareDraft",WH_PrepareDraft)
    work_history_graph.add_node("WH_PrepareOverallDraft",WH_PrepareOverallDraft)
    work_history_graph.add_node("WH_PresentForReview",WH_PresentForReview)
    work_history_graph.add_node("WH_AskInputsForRefinement",WH_AskInputsForRefinement)
    work_history_graph.add_node("WH_PrepareRefinementDraft",WH_PrepareRefinementDraft)
    work_history_graph.add_node("WH_StoreDB",WH_StoreDB)

    work_history_graph.add_conditional_edges("WH_PrepareDraft",WH_HasMoreProjects,{
        "next_project":"WH_SelectProject",
        "review":"WH_PrepareOverallDraft"
        # "review":"WH_PresentForReview"
    })
    
    work_history_graph.add_conditional_edges("WH_PresentForReview",WH_NeedRefinement,{
        "refine": "WH_AskInputsForRefinement",
        "store": "WH_StoreDB"
    })

    # work_history_graph.add_edge(START,"WH_PrepareQuestions")
    work_history_graph.add_edge(START,"WH_FlattenProjects")
    work_history_graph.add_edge("WH_FlattenProjects","WH_SelectProject")
    work_history_graph.add_edge("WH_SelectProject","WH_PrepareQuestions")
    work_history_graph.add_edge("WH_PrepareQuestions","WH_CollectAnswers")
    work_history_graph.add_edge("WH_CollectAnswers","WH_PrepareDraft")
    # work_history_graph.add_edge("WH_PrepareDraft","WH_PresentForReview")

    work_history_graph.add_edge("WH_PrepareOverallDraft","WH_PresentForReview")
    work_history_graph.add_edge("WH_AskInputsForRefinement","WH_PrepareRefinementDraft")
    work_history_graph.add_edge("WH_PrepareRefinementDraft","WH_PresentForReview")
    
    work_history_graph.add_edge("WH_StoreDB",END)

def WH_GRAPH():
    build_wh_graph()
    return work_history_graph.compile(checkpointer=get_checkpointer())