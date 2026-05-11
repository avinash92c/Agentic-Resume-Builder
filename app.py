from fastapi import FastAPI,HTTPException
import logging
from model import PersonalInfo
from userrepo import save_section,get_resume
import uuid
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
        save_section(session_id,"personal_info",data)
        return session_id
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save personal info: {e}") 