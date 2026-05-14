import logging
from dependencies import ConnectLLM
from pydantic import BaseModel,Field
from typing import Optional,List,TypedDict
from fastapi import FastAPI
from langchain.messages import SystemMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

#Dependencies objects
logger = logging.getLogger(__name__)
llm = ConnectLLM()

# gives  basic information asking for like name and age 
def  user_info():
    try:
        return None
    except Exception as ex:
        print (f"ex message here ")

#any filed of  expertise has to have  some experience regarless of  working with the enterprises or none
def user_total_experience_years(usrinput: str):    
    try:
        return None
    except Exception as ex:
        print (f"ex message here ")

# give user location preference by the user
def user_location_preference(location: str):
    try:
        return None
    except Exception as ex:
        print (f"ex message here ")

# what are the skills that you are specialiozed in eg  dotor : neurologist
def user_skill_set_list(userinput: str):
    try:
        return None
    except Exception as ex:
        print (f"ex message here ")

# this is like if you are a Doctor or an It engineer
def user_previous__secondary_expertise(userinput: str):
    try:
        return None
    except Exception as ex:
        print (f"ex message here ")

# what  he is working on  in the current company
def user_current_primary_expertise(userinput: str):
    try:
        return None
    except Exception as ex:
        print (f"ex message here ")

# this is like awards that were rewarded
def user_previous_industry_achievements(userinput: str):
    try:
        return None
    except Exception as ex:
        print (f"ex message here ")

# what  he is working on projects building/ learning things other than  that  company offers
def user_previous_personal_achievements(userinput: str):
    try:
        return None
    except Exception as ex:
        print (f"ex message here ")

#to get an analysis on the info  from LLM
def user_relevance_to_market(check: bool):
    try:
        return None
    except Exception as ex:
        print (f"ex message here ")

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
    name: str
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

# this is for LLM to work on
def ask_followup(state: WorkSkillSet) -> dict:
    return {
        "response_text": (
            "I want to make sure I help you accurately. "
            "Could you give me one more detail about what you need?"
        )
    }