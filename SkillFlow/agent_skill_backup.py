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
    refinement_questions: List[str]  # <-- Holds the 5 generated questions
    user_answers: dict[str, str]       # <-- Holds the user's answers
    refinements: List[str]
    approved: bool
    current_stage: str
    refinement_counts: int
    session_id: str

class SkillsPayload(BaseModel):
    skills_raw: str
    is_approved: bool

skills_graph = StateGraph(SkillState)

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
    # system_prompt = load_prompt(r"prompts\SkillFlow\refine_skills_queries.txt")
    # context = f"""
    # Original Background:
    # {state["raw_skills_input"]}
    # Current Draft:
    # {state["drafts"][-1]}
    # User Refinement Request:
    # {state["refinements"][-1]}
    # """
    """
    Reads the 5-question refinement queue and presents exactly ONE question 
    at a time to the user as a friendly chat prompt.
    """
    # Load the highly optimized agentic refinement prompt template
    system_prompt_template = load_prompt(r"prompts\SkillFlow\refine_skills_queries.txt")

    # Extract historical tracking strings safely
    current_draft = state["drafts"][-1] if state.get("drafts") else "No drafts compiled yet."
    latest_user_request = state["refinements"][-1] if state.get("refinements") else "No refinement specified."
    current_count = state.get("refinement_counts", 0) + 1  # Predict the upcoming attempt count

    # Inject variables dynamically into the template text
    system_prompt = system_prompt_template.format(
        raw_skills_input=state.get("raw_skills_input", ""),
        current_draft=current_draft,
        user_refinement_request=latest_user_request,
        refinement_count=current_count
    )

    # Compile clear engineering context for the message stream
    context = (
        f"Please execute the refinement request precisely. "
        f"Modify the current draft based on: '{latest_user_request}'"
    )

    logging.info(f"Refinement request: {state['refinements'][-1]}")
    logging.info(f"Current draft: {state['drafts'][-1]}")

    # Invoke your LLM connection
    result = llm.invoke([
        SystemMessage(content=system_prompt), 
        HumanMessage(content=context)
    ])
    logging.info(f"Refined compilation draft: {result.content}")

    return {
        "drafts": state.get("drafts", []) + [result.content],
        "current_stage": "pending_refinement_review"
    }

def Skills_ChatInterviewer(state: SkillState):
    """
    Dynamically fetches exactly ONE question from the generated queue 
    based on the current index pointer and halts for a user chat response.
    """
    idx = state.get("current_question_index", 0)
    questions = state.get("generated_questions", [])

    # Conditional Routing Checklist: Check if we have processed all questions
    if idx >= len(questions):
        return {"current_stage": "interviewer_complete"}

    # Extract precisely one question block
    active_question = questions[idx]

    # 🛑 Pause graph execution gracefully and stream a single chat query to the user
    user_response = interrupt({
        "question": active_question,
        "index": idx,
        "total": len(questions),
        "prompt": "Please type your answer to the question above."
    })

    # Capture user input text dynamically
    answers_backpack = state.get("user_answers", {})
    answers_backpack[active_question] = user_response.get("answer", "No answer provided.")

    return {
        "user_answers": answers_backpack,
        "current_question_index": idx + 1, # Increment pointer to the next question
        "current_stage": "awaiting_next_question"
    }

def Skills_CheckNextQuestion(state: SkillState):
    """Router function determining whether to continue the interview or draft."""
    idx = state.get("current_question_index", 0)
    questions = state.get("generated_questions", [])

    if idx < len(questions):
        return "continue_interview"
   #🎯 FIX: Return a clean key for the routing mapping below 
    return "compile_skills_draft"

def Skills_StoreDB(state: SkillState):
    final_draft = state["drafts"][-1] if state.get("drafts") else ""
    is_approved = state.get("approved", False)
    # structured_data = SkillsPayload(
    #     skills_raw=final_draft,
    #     is_approved=state.get("approved", False)
    # )                                          # ← missing this closing bracket
    # save_section(state['session_id'], "skills", structured_data.model_dump())
    save_section(state['session_id'], "skills", {
        "skills_raw": final_draft,
        "is_approved": is_approved
    })
   
    return {"current_stage": "Completed"}


def build_skills_graph():
    graph = StateGraph(SkillState)  # ← create graph INSIDE the function
    
    graph.add_node("Skills_CallLLM", Skills_CallLLM)
    graph.add_node("Skills_PresentForReview", Skills_PresentForReview)
    graph.add_node("Skills_ChatInterviewer", Skills_ChatInterviewer)
    graph.add_node("Skills_AskRefinements", Skills_AskRefinements)
    graph.add_node("Skills_StoreDB", Skills_StoreDB)

    graph.add_edge(START, "Skills_ChatInterviewer")
    graph.add_edge("Skills_CallLLM", "Skills_PresentForReview")

    graph.add_conditional_edges("Skills_PresentForReview", Skills_NeedRefinement, {
        "approved": "Skills_StoreDB", "refine": "Skills_AskRefinements"
    })
    graph.add_edge("Skills_AskRefinements", "Skills_PresentForReview")
    graph.add_edge("Skills_PresentForReview", "Skills_StoreDB")
    graph.add_edge("Skills_StoreDB", END)
    # Once an answer is registered, re-evaluate if the conversation needs to continue
    # graph.add_conditional_edges(
    # "Skills_ChatInterviewer",
    # Skills_CheckNextQuestion,
    # {
    #     "continue_interview": "Skills_ChatInterviewer",
    #    # 🎯 FIX: Route this key to your actual existing LLM Call Node
    #         "compile_skills_draft": "Skills_CallLLM"
    # })
    

    return graph

# Build and compile ONCE at import time
skills_app = build_skills_graph().compile(checkpointer=get_checkpointer())
