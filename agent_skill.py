import logging
from dependencies import ConnectLLM
from pydantic import BaseModel,Field
from typing import Optional,List


# gives  basic information asking for like name and age 
def  user_info():
    try:
        return None
    except Exception as ex:
        print (f"ex message here ")

#any filed of  expertise has to have  some experience regarless of  working with the enterprises or no
def user_total_experience_years(usrinput: str):    
    try:
        return None
    except Exception as ex:
        print (f"ex message here ")

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


class WorkExperience(BaseModel):
    company: str = Field(description="what is your current Comapny")
    role: str
    start_date: str
    end_date: Optional[str] = "Present"
    user_total_experience_years: str
    location: Optional[str]
    achievements: List[str] 
    technologies_used: List[str]
    user_relevance_to_market: bool


class SkillSet(BaseModel):
    name: str
    category: str  
    user_rating: int = 0 
    is_core: bool = False 