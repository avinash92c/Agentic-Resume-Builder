import logging
import json
from typing import List, TypedDict
from model import Resume
from dependencies import ConnectLLM, load_prompt, get_checkpointer
from userrepo import save_section,get_resume
from langgraph.types import interrupt
from langchain.messages import SystemMessage, HumanMessage
from langgraph.graph import START, END, StateGraph, MessagesState

logger = logging.getLogger(__name__)  # GET LOGGER

llm = ConnectLLM()

class FinalDraftState(MessagesState):
    session_id: str
    resume: Resume
    refinements: List[str]
    refinement_counts: int
    approved: bool
    drafts: List[str]
    current_stage: str

final_draft_graph = StateGraph(FinalDraftState)

def FD_FetchResumeParts(state: FinalDraftState):
    resume = get_resume(state["session_id"])
    return {
        "resume" : resume,
        "current_stage" : "fetch_details"
    }

def FD_PrepareDraft(state:FinalDraftState):
    system_prompt = load_prompt("prompts/FD/draft_prompt")
    resume = state["resume"]
    messages = [
        SystemMessage(system_prompt),
        HumanMessage(json.dumps(resume))
    ]

    result = llm.invoke(messages)
    logging.info(f"Result for Prepare Draft {result}")

    return {
        "drafts" : state.get("drafts",[])+[result.content],
        "current_stage" : "ready_for_review"
    }

def FD_PresentForReview(state:FinalDraftState):
    draft = state.get("drafts")[-1]
    answers = interrupt({
        "Question":"Please Review the Draft and confirm if approved or refinements needed",
        "draft":draft
    })
    logging.info(f"User Approved {answers['approved']}")
    return {
        "approved" : answers["approved"],
        "current_stage" : "received_user_input"
    }

def FD_NeedRefinement(state:FinalDraftState):
    # CONDITIONAL ROUTER NODE
    approved = state["approved"]
    if approved:
        return "store"
    elif state.get("refinement_counts",0) > 2 :
        return "store"
    else:
        return "refine"

def FD_AskRefinements(state:FinalDraftState):
    refinement_counts = state.get("refinement_counts",0)

    refinement = interrupt({
        "question" : "Please input you Refinement "
    })

    return {
        "refinements" : state.get("refinements",[]) + [refinement],
        "refinement_counts" : refinement_counts + 1,
        "current_stage": "ask_refinement"
    }

def FD_PrepareRefinedDraft(state:FinalDraftState):
    system_prompt = load_prompt("prompts\FD\/refine_draft")
    latest_draft = state["drafts"][-1]
    latest_refinement = state["refinements"][-1]

    human_prompt = f"""
        Latest Draft:
        {latest_draft}

        Latest Refinement:
        {latest_refinement}        
    """

    messages = [
        SystemMessage(system_prompt),
        HumanMessage(human_prompt)
    ]

    result = llm.invoke(messages)
    logging.info(f"Refined Draft {result.content}")

    return {
        "drafts" : state.get("drafts",[]) + [result.content],
        "current_stage" : "draft_refined"
    }

def FD_StoreDB(state:FinalDraftState):
    save_section(state['session_id'],"final_resume",state["drafts"][-1])
    return {"current_stage":"Completed"}

def build_fd_graph():
    final_draft_graph.add_node("FD_FetchResumeParts",FD_FetchResumeParts)
    final_draft_graph.add_node("FD_PrepareDraft",FD_PrepareDraft)
    final_draft_graph.add_node("FD_PresentForReview",FD_PresentForReview)
    final_draft_graph.add_node("FD_AskRefinements",FD_AskRefinements)
    final_draft_graph.add_node("FD_PrepareRefinedDraft",FD_PrepareRefinedDraft)
    final_draft_graph.add_node("FD_StoreDB",FD_StoreDB)
    
    final_draft_graph.add_conditional_edges("FD_PresentForReview",FD_NeedRefinement,{
        "store":"FD_StoreDB",
        "refine":"FD_AskRefinements"
    })

    final_draft_graph.add_edge(START,"FD_FetchResumeParts")
    final_draft_graph.add_edge("FD_FetchResumeParts","FD_PrepareDraft")
    final_draft_graph.add_edge("FD_PrepareDraft","FD_PresentForReview")

    final_draft_graph.add_edge("FD_AskRefinements","FD_PrepareRefinedDraft")
    final_draft_graph.add_edge("FD_PrepareRefinedDraft","FD_PresentForReview")

    final_draft_graph.add_edge("FD_StoreDB",END)

def FINAL_GRAPH():
    build_fd_graph()
    return final_draft_graph.compile(checkpointer=get_checkpointer())

