from fastapi import FastAPI,HTTPException,Response
import logging
from model import PersonalInfo,Education,Certifications,StartRequest,ResumeRequest
from userrepo import save_section,get_resume_by_email
import uuid
from typing import List
from pymongo.errors import PyMongoError
from agent_psg import PSG_GRAPH
from agent_wh import WH_GRAPH
from agent_pp import PP_GRAPH
from langgraph.types import Command

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

app = FastAPI()

psg_graph = PSG_GRAPH()
wh_graph = WH_GRAPH()
pp_graph = PP_GRAPH()

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

@app.post("/psg/start")
async def start_psg(request: StartRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    resume = get_resume_by_email(request.email)
    psg_graph.invoke(
        {"user_input_initial": request.user_input,"session_id":resume.sessionId},
        config=config
    )
    
    # don't use invoke's return value — get state separately after interrupt
    state = psg_graph.get_state(config)
    
    return {
        "thread_id": thread_id,
        "stage": state.values["current_stage"],
        "questions": state.tasks[0].interrupts[0].value["questions"]
    }

@app.post("/psg/resume")
async def resume_psg(request: ResumeRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    
    psg_graph.invoke(
        Command(resume=request.user_data),  # not user_input, resume with answers
        config=config
    )
    
    state = psg_graph.get_state(config)
    logging.info(f"Drafts {state}")
    
    # graph may or may not be interrupted again depending on stage
    is_interrupted = bool(state.tasks)
    
    return {
        "thread_id": request.thread_id,
        "stage": state.values["current_stage"],
        # "data": state.values["drafts"][-1],
        "data": state.tasks[0].interrupts[0].value if is_interrupted else None,
        "complete": not is_interrupted
    }

@app.get("/psg/view")
async def view_psg_graph():
    png_bytes = psg_graph.get_graph().draw_mermaid_png()
    return Response(content=png_bytes, media_type="image/png")

@app.get("/wh/view")
async def view_wh_graph():
    png_bytes = wh_graph.get_graph().draw_mermaid_png()
    return Response(content=png_bytes, media_type="image/png")

@app.post("/wh/start")
async def start_psg(request: StartRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    resume = get_resume_by_email(request.email)
    wh_graph.invoke(
        {"user_input_initial": request.user_input,"session_id":resume.sessionId},
        config=config
    )
    
    # don't use invoke's return value — get state separately after interrupt
    state = wh_graph.get_state(config)
    
    return {
        "thread_id": thread_id,
        "stage": state.values["current_stage"],
        "questions": state.tasks[0].interrupts[0].value["questions"]
    }

@app.post("/wh/resume")
async def resume_psg(request: ResumeRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    
    wh_graph.invoke(
        Command(resume=request.user_data),  # not user_input, resume with answers
        config=config
    )
    
    state = wh_graph.get_state(config)
    logging.info(f"Drafts {state}")
    
    # graph may or may not be interrupted again depending on stage
    is_interrupted = bool(state.tasks)
    
    return {
        "thread_id": request.thread_id,
        "stage": state.values["current_stage"],
        # "data": state.values["drafts"][-1],
        "data": state.tasks[0].interrupts[0].value if is_interrupted else None,
        "complete": not is_interrupted
    }

@app.get("/pp/view")
async def view_pp_graph():
    png_bytes = pp_graph.get_graph().draw_mermaid_png()
    return Response(content=png_bytes, media_type="image/png")

@app.post("/pp/start")
async def start_psg(request: StartRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    resume = get_resume_by_email(request.email)
    pp_graph.invoke(
        {"user_input_initial": request.user_input,"session_id":resume.sessionId},
        config=config
    )
    
    # don't use invoke's return value — get state separately after interrupt
    state = pp_graph.get_state(config)
    
    return {
        "thread_id": thread_id,
        "stage": state.values["current_stage"],
        "questions": state.tasks[0].interrupts[0].value["questions"]
    }

@app.post("/pp/resume")
async def resume_psg(request: ResumeRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    
    pp_graph.invoke(
        Command(resume=request.user_data),  # not user_input, resume with answers
        config=config
    )
    
    state = pp_graph.get_state(config)
    logging.info(f"Drafts {state}")
    
    # graph may or may not be interrupted again depending on stage
    is_interrupted = bool(state.tasks)
    
    return {
        "thread_id": request.thread_id,
        "stage": state.values["current_stage"],
        # "data": state.values["drafts"][-1],
        "data": state.tasks[0].interrupts[0].value if is_interrupted else None,
        "complete": not is_interrupted
    }