import logging
import json
from typing import List, TypedDict
from dependencies import ConnectLLM, load_prompt, get_checkpointer
from userrepo import save_section
from langgraph.types import interrupt
from langchain.messages import SystemMessage, HumanMessage
from langgraph.graph import START, END, StateGraph, MessagesState

logger = logging.getLogger(__name__)  # GET LOGGER

llm = ConnectLLM()

class PersonalProjectsState(MessagesState):
    session_id: str
    user_input_projects: List[str] # PROJECT WISE DETAILS
    current_project_index: int # project being processed now,
    refined_projects: List[str]
    refinement_counts: int
    generated_questions: List[str] # PROJECT WISE QUESTIONS
    user_answers: dict[str, str] # PROJECT WISE QUESTION AND ANSWERS
    refinements: List[str] # REFINEMENTS
    # WILL CONTAIN ALL THREE DRAFT VERSIONS IN SEQUENCE. LAST DRAFT WILL BE THE FINAL DRAFT
    drafts: List[str] #REFINED DRAFTS
    approved: bool
    current_stage: str

class GeneratedQuestionsResult(TypedDict):
    questions: dict[str, List[str]]

personal_projects_graph = StateGraph(PersonalProjectsState)

def PP_SelectProject(state:PersonalProjectsState):
    # PICKS ONE PROJECT AT A TIME AND ASKS CURATED QUESTIONS
    current_index = state.get("current_project_index", 0)
    # refined_projects = state.get("refined_projects", [])

    return{
        "current_project_index":current_index,
        # "refined_projects": refined_projects,
        "current_state": "select_project"
    }

def PP_PrepareQuestions(state:PersonalProjectsState):
    system_prompt = load_prompt("prompts\PP\prepare_questions.txt")
    current_project_index = state["current_project_index"]
    user_input_projects = state["user_input_projects"]

    current_project = user_input_projects[current_project_index]

    messages = [
        HumanMessage(current_project),
        SystemMessage(system_prompt)
    ]

    result = llm.with_structured_output(GeneratedQuestionsResult).invoke(messages)
    logging.info(f"PP_PrepareQuestions result {result}")
    return {
        "generated_questions":result["questions"],
        "current_state":"awaiting_answers"
    }

def PP_CollectAnswers(state:PersonalProjectsState):
    # TAKES ASKED QUESTION AND ANSWERS AND PASSES TO LLM TO GENERATE DRAFT
    questions = state["generated_questions"]
    answers = interrupt({
        "questions":questions
    })
    return {
        "user_answers":answers,
        "current_state":"ready_for_project_draft"
    }

def PP_PrepareProjectDraft(state:PersonalProjectsState):
    system_prompt = load_prompt("prompts/PP/initial_project_draft.txt")
    current_project_index = state["current_project_index"]
    user_input_projects = state["user_input_projects"]
    refined_projects = state.get("refined_projects",[]).copy()
    selected_project = user_input_projects[current_project_index]

    qa_pairs = "\n".join(
        f"Q: {q}\nA: {state['user_answers'].get(q, 'No answer')}"
        for q in state["generated_questions"]
    )
    
    context = f"""
    Personal Project History:
    {selected_project}
    Questions and Answers:
    {qa_pairs}
    """

    messages = [
        SystemMessage(system_prompt),
        HumanMessage(context)
    ]

    result = llm.invoke(messages)
    refined_projects.append(result.content)

    return {
        "current_project_index": current_project_index+1,
        "refined_projects":refined_projects,        
        "current_state":"select_next_project"
    }

def PP_HasMoreProjects(state:PersonalProjectsState):
    input_projects = state["user_input_projects"]
    current_project_index = state["current_project_index"]

    if current_project_index<len(input_projects)-1:
        return "next_project"
    else:
        return "review"    

def PP_PrepareOverallDraft(state:PersonalProjectsState):
    system_prompt = load_prompt("prompts/PP/overall_draft.txt")
    refined_projects = state["refined_projects"]
    refined_prompts_text = json.dumps(refined_projects)
    drafts = state.get("drafts",[])

    messages = [
        SystemMessage(system_prompt),
        HumanMessage(refined_prompts_text)
    ]

    result = llm.invoke(messages)
    drafts.append(result.content)

    return {
        "drafts":drafts,
        "current_state":"ready_for_review"
    }

def PP_ReviewOverallDraft(state:PersonalProjectsState):
    draft = state["drafts"][-1]
    approved = interrupt({
        "draft": draft,
        "question": "Do you need further refinments?"
    })

    return {
        "approved":approved["approved"],
        "current_state":"check_refinement"
    }

def PP_NeedRefinement(state:PersonalProjectsState):
    approved = state.get("approved",False)
    if approved:
        return "store"
    else:
        return "refine"

def PP_AskInputsForRefinement(state:PersonalProjectsState):
    draft = state["drafts"][-1]

    refinement = interrupt({
        "draft": draft,
        "question":"Please input your refinements"
    })
    
    existing = state.get("refinements") or []
    
    return {
        "refinements": existing + [refinement["refinement"]],
        "refinement_counts": state.get("refinement_counts", 0) + 1,
        "current_stage":"refinement"
    }

def PP_PrepareRefinementDraft(state:PersonalProjectsState):
    refinement = state["refinements"][-1]
    draft = state["drafts"][-1]
    user_input_projects = json.dumps(state["user_input_projects"])
    system_prompt = load_prompt("prompts\PP\/refine_draft.txt")
        
    human_message = f"""
    Original Background: {user_input_projects}

    Draft: {draft}

    Refinement: {refinement}
    """

    messages = [
        SystemMessage(system_prompt),
        HumanMessage(human_message)
    ]

    result = llm.invoke(messages)

    return {
        "drafts": state.get("drafts", []) + [result.content],
        "current_stage": "pending_refinement_review"
    }

def PP_StoreDB(state:PersonalProjectsState):
    session_id = state["session_id"]
    final_draft = state["drafts"][-1]
    save_section(session_id,"personal_projects",final_draft)
    return {"current_stage":"Completed"}

def build_pp_graph():
    personal_projects_graph.add_node("PP_SelectProject",PP_SelectProject)
    personal_projects_graph.add_node("PP_PrepareQuestions",PP_PrepareQuestions)
    personal_projects_graph.add_node("PP_CollectAnswers",PP_CollectAnswers)
    personal_projects_graph.add_node("PP_PrepareProjectDraft",PP_PrepareProjectDraft)

    personal_projects_graph.add_node("PP_PrepareOverallDraft",PP_PrepareOverallDraft)
    personal_projects_graph.add_node("PP_ReviewOverallDraft",PP_ReviewOverallDraft)

    personal_projects_graph.add_node("PP_AskInputsForRefinement",PP_AskInputsForRefinement)
    personal_projects_graph.add_node("PP_PrepareRefinementDraft",PP_PrepareRefinementDraft)

    personal_projects_graph.add_node("PP_StoreDB",PP_StoreDB)

    personal_projects_graph.add_conditional_edges("PP_PrepareProjectDraft",PP_HasMoreProjects,{
        "next_project":"PP_SelectProject",
        "review":"PP_PrepareOverallDraft"
    })

    personal_projects_graph.add_conditional_edges("PP_ReviewOverallDraft",PP_NeedRefinement,{
        "refine": "PP_AskInputsForRefinement",
        "store": "PP_StoreDB"
    })

    personal_projects_graph.add_edge(START,"PP_SelectProject")
    personal_projects_graph.add_edge("PP_SelectProject","PP_PrepareQuestions")
    personal_projects_graph.add_edge("PP_PrepareQuestions","PP_CollectAnswers")
    personal_projects_graph.add_edge("PP_CollectAnswers","PP_PrepareProjectDraft")

    personal_projects_graph.add_edge("PP_PrepareOverallDraft","PP_ReviewOverallDraft")
    personal_projects_graph.add_edge("PP_AskInputsForRefinement","PP_PrepareRefinementDraft")
    personal_projects_graph.add_edge("PP_PrepareRefinementDraft","PP_ReviewOverallDraft")

    personal_projects_graph.add_edge("PP_StoreDB",END)

def PP_GRAPH():
    build_pp_graph()
    return personal_projects_graph.compile(checkpointer=get_checkpointer())