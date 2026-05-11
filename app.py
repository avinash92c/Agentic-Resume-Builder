from fastapi import FastAPI,HTTPException
import logging
from model import PersonalInfo,Education,Certifications
from userrepo import save_section,get_resume,get_resume_by_email
import uuid
from typing import List
from pymongo.errors import PyMongoError

logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s: %(message)s'
)

app = FastAPI()

@app.get("/health")
def health():
    """Health Check

    Returns:
        str : Ok
    """
    return "Ok"

@app.get("/pages")
def pages():
    """returns the list of pages available. For use in UI. Each Page refers to a sub agent flow

    Returns:
        map : returns an map of pages available in the system
    """

    pages = {
        "Core": ["Personal Info","Professional Summary","Skills","Professional Experience","Certifications","Education","Review"],
        "Cover Letter":["Cover Letter"],
        "Job Fit":["Job Fit"],
        "Assessment":["Assessment","Learning Roadmap"]
    }

    return pages

@app.post("/personal-info")
def savepersonalinfo(data:PersonalInfo):
    # START SESSION WITH A UNIQUE ID AND SAVE PERSONAL INFO. HOW ABOUT A UUID
    try:
        session_id = str(uuid.uuid4())
        save_section(session_id,"personal_info",data.model_dump())
        return session_id
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save personal info: {e}") 
    

@app.get("/personal-info")
def getPersonalInfo(email: str):
    try:
        resume =get_resume_by_email(email)
        return resume.personalInfo
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Failed to get personal info: {e}") 
    

@app.post("/education-info")
def saveeducationinfo(educate: List[Education],email : str):
    try:
        resume =get_resume_by_email(email)
        session_id =resume.sessionId
        save_section(session_id,"education",[item.model_dump() for item in educate])
        return session_id
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save personal info: {e}") 
    

@app.get("/education-info")
def geteducationinfo(email : str):
    try:
        resume =get_resume_by_email(email)
        return resume.education
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Failed to get personal info: {e}") 
    

@app.post("/certification-info")
def savecertificationinfo(certificate :List[Certifications],email: str):
    try:
        resume =get_resume_by_email(email)
        session_id =resume.sessionId
        save_section(session_id,"certificates",[ item.model_dump() for item in certificate])
        return session_id
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save personal info: {e}") 
    
@app.get("/certification-info")
def getCertificatedinfo(email:str):
    try:
        print(email)
        resume =get_resume_by_email(email)
        print(resume)
        return resume.certificates
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Failed to get personal info: {e}") 
