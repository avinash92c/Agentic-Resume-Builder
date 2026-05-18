import logging
from dependencies import ConnectLLM,load_prompt
from pydantic import BaseModel,Field
from typing import Optional,List,TypedDict,Literal
from fastapi import FastAPI
from langchain.messages import SystemMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from userrepo import save_section

#Dependencies objects
logger = logging.getLogger(__name__)
llm = ConnectLLM()

class GeneratedQuestionsResult(TypedDict):
    questions: List[str]
    resume_text: str
    skill_queue: List[str]          # Skills left to test
    current_skill: str              # Skill currently being evaluated
    current_question: str           # The generated question
    user_answer: str                # User's input response
    evaluations: Dict[str, Any]     # Stores results for each skill
    years_of_experience: int

# gives  basic information asking for like name and age 
def  user_info():
    try:
        return None
    except Exception as ex:
        print (f"ex message here ")

# #any filed of  expertise has to have  some experience regarless of  working with the enterprises or none
# def user_total_experience_years(usrinput: str):    
#     try:
#         return None
#     except Exception as ex:
#         print (f"ex message here ")

# # give user location preference by the user
# def user_location_preference(location: str):
#     try:
#         return None
#     except Exception as ex:
#         print (f"ex message here ")

# # what are the skills that you are specialiozed in eg  dotor : neurologist
# def user_skill_set_list(userinput: str):
#     try:
#         return None
#     except Exception as ex:
#         print (f"ex message here ")

# # this is like if you are a Doctor or an It engineer
# def user_previous__secondary_expertise(userinput: str):
#     try:
#         return None
#     except Exception as ex:
#         print (f"ex message here ")

# # what  he is working on  in the current company
# def user_current_primary_expertise(userinput: str):
#     try:
#         return None
#     except Exception as ex:
#         print (f"ex message here ")

# # this is like awards that were rewarded
# def user_previous_industry_achievements(userinput: str):
#     try:
#         return None
#     except Exception as ex:
#         print (f"ex message here ")

# # what  he is working on projects building/ learning things other than  that  company offers
# def user_previous_personal_achievements(userinput: str):
#     try:
#         return None
#     except Exception as ex:
#         print (f"ex message here ")

# #to get an analysis on the info  from LLM
# def user_relevance_to_market(check: bool):
#     try:
#         return None
#     except Exception as ex:
#         print (f"ex message here ")

# first draft of the resume to be idenitfied
def  user_review():
    try:
        return None
    except Exception as ex:
        print (f"ex message here ")

# rating the user based on all the information provided and gets a brief about the skills that he posses to the current market
def user_rating():
    try:
        return None
    except Exception as ex:
        print (f"ex message here ")

class WorkSkillSet(TypedDict):
    user_info_data: str
    category: str  
    user_rating: int
    is_core: bool 
    company: str 
    role: str
    start_date: str
    end_date: Optional[str] 
    user_total_experience_years: str
    location: Optional[str]
    achievements: List[str] 
    technologies_used: List[str]
    user_relevance_to_market: bool  
    reponseinfo :str
    flowmap: str
    
def extract_skills_node(state: GeneratedQuestionsResult) -> GeneratedQuestionsResult:
    print("Extracting Skills")
    text = state["resume_text"]

    # use an LLM with structured output to parse the text.
    extracted_skills = ["Python", "C#", "Design"]
    state["skill_queue"] = extracted_skills
    state["evaluations"] = {}
    return state

def classify_request(state: WorkSkillSet) -> dict:
    text = state["user_info_data"].lower()
    if "IT" in text or "CSE" in text:
        return {"flowmap": "approval"}
    if "unclear" in text or "maybe" in text:
        return {"flowmap": "clarify"}
    return {"flowmap": "answer"}

def generate_question_node(state: GeneratedQuestionsResult) -> GeneratedQuestionsResult:
    queue = state["skill_queue"].copy()
    current_skill = queue.pop(0)
    yoe = state.get("years_of_experience", 5)
    
    if current_skill == "Python":
        question = "Explain how you would troubleshoot a memory leak caused by dangling references or global variables in a long-running Python application."
    elif current_skill == "C#":
        question = "Design an efficient LRU Cache eviction strategy. What data structures would you combine to achieve O(1) lookups and updates?"
    else:
        question = f"Describe a complex architectural trade-off you had to make recently when designing a system leveraging {current_skill}."
        
    state["skill_queue"] = queue 
    state["current_skill"] = current_skill
    state["current_question"] = question
    print(f"[Question]: {question}")
    state["user_answer"] = input(">> ")
    
    return state

def draft_answer(state: WorkSkillSet) -> dict:
        system_prompt = load_prompt("prompts\SkillFlow\machinequeries.txt")
        prompt = (
        "score": 4.5,
        "feedback": "Demonstrated solid technical grasp of the core concepts, though could expand on micro-optimization metrics.",
        "missing_keywords": ["tracemalloc", "weakref"] if state["current_skill"] == "Python" else []
        "You are a helpful resume builder is a support assistant to write perfect resumes .\n"
        "ananlyse the  uploaded resumes agianst the list of skills provided .\n"
        "Answer the following question clearly and in maximum of 2 line.\n\n"
        f"Customer question: {state['user_info_data']}"
          )
        
        llm_messages = [
        SystemMessage(system_prompt),
        HumanMessage(prompt)
        ]
               
        result = llm.with_structured_output(GeneratedQuestionsResult).invoke(llm_messages)
        # response = client.chat.completions.create(
        # model="llama-3.1-8b-instant",
        # messages=[{"role": "user", "content": prompt}], )
        # result
        state["evaluations"][state["current_skill"]] = prompt
          
        return state


# this is for human  to answer on
def ask_followup(state: WorkSkillSet) -> dict:
    return {
        "response_text": (
            "I want to make sure I help you accurately. "
            "Could you give me one more detail about what you need?"
        )
    }

def choose_next_step(state: WorkSkillSet) -> Literal["ask_followup", "draft_answer", "approval_gate"]:
    route_map = {
        "clarify": "ask_followup",
        "approval": "accept_results",
        "answer": "draft_answer",
    }
    return route_map.get(state["flowmap"], "draft_answer")


def store_db_gate(state:WorkSkillSet):
    save_section(state['reponseinfo'],"flow",state["flowmap"]
    return {"current_stage":"Completed"}

skillbuilder = StateGraph(WorkSkillSet)
skillbuilder.add_node("extract_skills", extract_skills_node)
skillbuilder.add_node("generate_question", generate_question_node)
skillbuilder.add_node("evaluate_answer", evaluate_answer_node)
skillbuilder.add_node("classify_request", classify_request)
skillbuilder.add_node("ask_followup", ask_followup)
skillbuilder.add_node("draft_answer", draft_answer)
skillbuilder.add_node("accept_results", accept_results)

skillbuilder.add_edge(START, "classify_request")
skillbuilder.add_conditional_edges("classify_request", "choose_next_step")
skillbuilder.add_conditional_edges("choose_next_step", "extract_skills")
skillbuilder.add_conditional_edges("extract_skills", "generate_question")
skillbuilder.add_conditional_edges("generate_question", "evaluate_answer")

builder.add_conditional_edges(
    "evaluate_answer",
    route_based_on_queue,
    {
        "generate_question": "generate_question",
        "end_graph": END
    }
)
skillbuilder.add_edge("ask_followup", END)
skillbuilder.add_edge("draft_answer", END)
skillbuilder.add_edge("accept_results", END)

app = skillbuilder.compile()

print("Starting Agentic Skill Checker Graph")
final_output = graph.invoke({}])