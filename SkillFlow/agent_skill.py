import logging
from dependencies import ConnectLLM, load_prompt, get_checkpointer
from pydantic import BaseModel,Field
from typing import List,Optional,TypedDict,Literal
from fastapi import FastAPI
from langchain.messages import SystemMessage, HumanMessage
from langgraph.types import interrupt
from langgraph.graph import END, START, MessagesState, StateGraph
from userrepo import save_section
from langgraph.types import Command

#Dependencies objects
logger = logging.getLogger(__name__)
llm = ConnectLLM()

class SkillState(MessagesState):
    raw_skills_input: str
    drafts: List[str]
    refinements: List[str]
    approved: bool
    current_stage: str
    refinement_counts: int
    session_id: str

class SkillsPayload(BaseModel):
    skills_raw: str
    is_approved: bool

# skills_graph = StateGraph(SkillState)

def Skills_CallLLM(state: SkillState):
    system_prompt = load_prompt(r"prompts\SkillFlow\machinequeries.txt")  # ← add this back
    
    drafts = state.get("drafts") or []
    refinements = state.get("refinements") or []
    last_refinement = refinements[-1] if refinements else "Initial generation, no refinements yet"

    context = f"""
    Original Background:
    {state["raw_skills_input"]}

    User Refinement Request:
    {last_refinement}
    """
    logging.info(f"Refinement: {last_refinement}")
    logging.info(f"Current draft: {drafts[-1] if drafts else 'No draft yet'}")

    logging.info(f"Processing initial skill generation / update.")
    result = llm.invoke([SystemMessage(system_prompt), HumanMessage(context)])

    logging.info(f"Refined draft: {result.content}")

    return {
        "drafts": drafts + [result.content],
        "current_stage": "pending_refinement_review"
    }

def Skills_PresentForReview(state: SkillState):
    refinement = interrupt({
        "drafts": state.get("drafts", [])[-1] if state.get("drafts") else "No draft generated yet.",
        "message": "Review the extracted skills. Provide feedback or approve."
    })
    
    is_approved = refinement.get("approved", False)
    refinement_text = refinement.get("refinement", None)

    existing_refinements = state.get("refinements") or []
    if refinement_text:
        existing_refinements = existing_refinements + [refinement_text]

    return {
        "refinements": existing_refinements,
        "approved": is_approved,  # read approved from frontend
        "refinement_counts": state.get("refinement_counts", 0) + (1 if not is_approved and refinement_text else 0),
        "current_stage": "refinement"
    }

def Skills_NeedRefinement(state:SkillState):
    if state.get("approved", False):
        return "approved"
    elif state.get("refinement_counts", 0) < 2:
        return "refine"
    else:
        # Graceful escape route: automatically store once credit runs dry
        logging.warning("User hit max refinement allowance (2). Shipping current draft.")
        return "approved"
    
def Skills_AskRefinements(state : SkillState):
    system_prompt = load_prompt(r"prompts\PSG\refine_draft.txt")

    context = f"""
    Original Background:
    {state["raw_skills_input"]}

    Current Draft:
    {state["drafts"][-1]}

    User Refinement Request:
    {state["refinements"][-1]}
    """

    logging.info(f"Refinement request: {state['refinements'][-1]}")
    logging.info(f"Current draft: {state['drafts'][-1]}")

    result = llm.invoke([SystemMessage(system_prompt), HumanMessage(context)])
    logging.info(f"Refined compilation draft: {result.content}")

    return {
        "drafts": state.get("drafts", []) + [result.content],
        "current_stage": "pending_refinement_review"
    }


def Skills_StoreDB(state:SkillState):
    # save_section(state['session_id'],"skills",state["drafts"][-1])
    final_draft = state["drafts"][-1] if state.get("drafts") else ""

    # Pack the raw string into a dictionary payload
    # payload = {"skills_content": final_draft}
    # save_section(state['session_id'], "skills", payload)

    structured_data = SkillsPayload(
        skills_raw=final_draft,
        is_approved=state.get("approved", False)

    # .model_dump() converts your Pydantic object into a clean dict
    save_section(state['session_id'], "skills", structured_data.model_dump())

    return {"current_stage":"Completed"}

def build_skills_graph():
    graph = StateGraph(SkillState)  # ← create graph INSIDE the function
    
    graph.add_node("Skills_CallLLM", Skills_CallLLM)
    graph.add_node("Skills_PresentForReview", Skills_PresentForReview)
    graph.add_node("Skills_AskRefinements", Skills_AskRefinements)
    graph.add_node("Skills_StoreDB", Skills_StoreDB)

    graph.add_edge(START, "Skills_CallLLM")
    graph.add_edge("Skills_CallLLM", "Skills_PresentForReview")
    graph.add_conditional_edges("Skills_PresentForReview", Skills_NeedRefinement, {
        "approved": "Skills_StoreDB", "refine": "Skills_AskRefinements"
    })
    graph.add_edge("Skills_AskRefinements", "Skills_PresentForReview")
    graph.add_edge("Skills_PresentForReview", "Skills_PresentForReview")
    graph.add_edge("Skills_StoreDB", END)
    
    return graph

# Build and compile ONCE at import time
skills_app = build_skills_graph().compile(checkpointer=get_checkpointer())
