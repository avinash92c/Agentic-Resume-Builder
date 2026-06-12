from fastapi import FastAPI,HTTPException,Response
from fastapi.middleware.cors import CORSMiddleware
import logging

from pydantic import BaseModel
from model import CertificationsRequest, EducationInfoRequest, PersonalInfo,Education,Certifications,StartRequest,ResumeRequest
from userrepo import save_section,get_resume_by_email
import uuid
from typing import List
from pymongo.errors import PyMongoError
from agent_psg import PSG_GRAPH
from agent_wh import WH_GRAPH,WorkExperience
from agent_pp import PP_GRAPH
from agent_final import FINAL_GRAPH
from langgraph.types import Command
from model import AgentResponse, AgentResponseData
from responsebuilder import map_interrupt_data

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

class WorkHistoryStartRequest(BaseModel):
    email: str
    user_input: List[WorkExperience]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

psg_graph = PSG_GRAPH()
wh_graph = WH_GRAPH()
pp_graph = PP_GRAPH()
fd_graph = FINAL_GRAPH()

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
        resume =get_resume_by_email (email)
        return resume.personalInfo
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Failed to get personal info: {e}") 
    

@app.post("/education-info")
def saveeducationinfo(education:EducationInfoRequest):
    try:
        resume = get_resume_by_email(education.email)
        session_id = resume.sessionId
        save_section(session_id,"education",[item.model_dump() for item in education.education])
        return session_id
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save personal info: {e}") 
    

@app.get("/education-info")
def geteducationinfo(email : str):
    try:
        resume = get_resume_by_email(email)
        return resume.education
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Failed to get personal info: {e}") 
    

@app.post("/certification-info")
def savecertificationinfo(request:CertificationsRequest):
    try:
        resume = get_resume_by_email(request.email)
        session_id = resume.sessionId
        save_section(session_id,"certificates",[ item.model_dump() for item in request.certifications])
        return session_id
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save personal info: {e}") 
    
@app.get("/certification-info")
def getCertificatedinfo(email:str):
    try:
        print(email)
        resume = get_resume_by_email(email)
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
    interrupt_data = (
        state.tasks[0].interrupts[0].value
    )
    
    # return {
    #     "thread_id": thread_id,
    #     "stage": state.values["current_stage"],
    #     "questions": state.tasks[0].interrupts[0].value["questions"]
    # }

    return AgentResponse(
        thread_id=thread_id,
        stage=state.values["current_stage"],
        complete=False,
        data=map_interrupt_data(interrupt_data)
    )

@app.post("/psg/resume", response_model=AgentResponse)
async def resume_psg(request: ResumeRequest):

    config = {
        "configurable": {
            "thread_id": request.thread_id
        }
    }

    psg_graph.invoke(
        Command(resume=request.user_data),
        config=config
    )

    state = psg_graph.get_state(config)

    logging.info(f"Drafts {state}")

    is_interrupted = bool(state.tasks)

    if is_interrupted:

        interrupt_data = (
            state.tasks[0].interrupts[0].value
        )

        logging.info(f"Interrupt Data {interrupt_data}")

        return AgentResponse(
            thread_id=request.thread_id,
            stage=state.values["current_stage"],
            complete=False,
            data=map_interrupt_data(interrupt_data)
        )

    drafts = state.values.get("drafts", [])

    latest_draft = drafts[-1] if drafts else None

    return AgentResponse(
        thread_id=request.thread_id,
        stage=state.values["current_stage"],
        complete=True,
        data=AgentResponseData(
            message="Professional summary completed successfully.",
            draft=latest_draft
        )
    )

# @app.post("/psg/resume")
# async def resume_psg(request: ResumeRequest):
#     config = {"configurable": {"thread_id": request.thread_id}}
    
#     psg_graph.invoke(
#         Command(resume=request.user_data),  # not user_input, resume with answers
#         config=config
#     )
    
#     state = psg_graph.get_state(config)
#     logging.info(f"Drafts {state}")
    
#     # graph may or may not be interrupted again depending on stage
#     is_interrupted = bool(state.tasks)
    
#     return {
#         "thread_id": request.thread_id,
#         "stage": state.values["current_stage"],
#         # "data": state.values["drafts"][-1],
#         "data": state.tasks[0].interrupts[0].value if is_interrupted else None,
#         "complete": not is_interrupted
#     }

@app.get("/psg/view")
async def view_psg_graph():
    png_bytes = psg_graph.get_graph().draw_mermaid_png()
    return Response(content=png_bytes, media_type="image/png")

@app.get("/wh/view")
async def view_wh_graph():
    png_bytes = wh_graph.get_graph().draw_mermaid_png()
    return Response(content=png_bytes, media_type="image/png")

@app.post("/wh/start")
async def start_wh(request: WorkHistoryStartRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    resume = get_resume_by_email(request.email)
    wh_graph.invoke(
        {"user_input_initial": request.user_input,"session_id":resume.sessionId},
        config=config
    )
    
    # don't use invoke's return value — get state separately after interrupt
    state = wh_graph.get_state(config)
    interrupt_data = (
        state.tasks[0].interrupts[0].value
    )
    
    # return {
    #     "thread_id": thread_id,
    #     "stage": state.values["current_stage"],
    #     "questions": state.tasks[0].interrupts[0].value["questions"]
    # }

    stage = state.values["current_stage"]

    logging.info(f"stage - {stage}")

    if stage != "error":
        return AgentResponse(
            thread_id=thread_id,
            stage=stage,
            complete=False,
            data=map_interrupt_data(interrupt_data)
        )
    else:
        logging.exception("WH start failed")

        raise HTTPException(
            status_code=500,
            detail=str("error")
        )

# @app.post("/wh/resume")
# async def resume_wh(request: ResumeRequest):
#     config = {"configurable": {"thread_id": request.thread_id}}
    
#     wh_graph.invoke(
#         Command(resume=request.user_data),  # not user_input, resume with answers
#         config=config
#     )
    
#     state = wh_graph.get_state(config)
#     logging.info(f"Drafts {state}")
    
#     # graph may or may not be interrupted again depending on stage
#     is_interrupted = bool(state.tasks)
    
#     return {
#         "thread_id": request.thread_id,
#         "stage": state.values["current_stage"],
#         # "data": state.values["drafts"][-1],
#         "data": state.tasks[0].interrupts[0].value if is_interrupted else None,
#         "complete": not is_interrupted
#     }

@app.post("/wh/resume")
async def resume_wh(request: ResumeRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    
    wh_graph.invoke(
        Command(resume=request.user_data),  # not user_input, resume with answers
        config=config
    )

    state = wh_graph.get_state(config)
    logging.info(f"Drafts {state}")

    # graph may or may not be interrupted again depending on stage
    is_interrupted = bool(state.tasks)
    stage=state.values["current_stage"]

    if stage=="error":
        raise HTTPException(
            status_code=500,
            detail=str("error")
        )

    if is_interrupted:
        interrupt_data = (
            state.tasks[0].interrupts[0].value
        )

        logging.info(f"Interrupt Data {interrupt_data}")

        return AgentResponse(
            thread_id=request.thread_id,
            stage=stage,
            complete=False,
            data=map_interrupt_data(interrupt_data)
        )
    
    drafts = state.values.get("drafts", [])
    latest_draft = drafts[-1] if drafts else None

    return AgentResponse(
        thread_id=request.thread_id,
        stage=stage,
        complete=True,
        data=AgentResponseData(
            message="Work History Summary completed successfully.",
            draft=latest_draft
        )
    )


@app.get("/pp/view")
async def view_pp_graph():
    png_bytes = pp_graph.get_graph().draw_mermaid_png()
    return Response(content=png_bytes, media_type="image/png")

@app.post("/pp/start")
async def start_pp(request: StartRequest):
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
async def resume_pp(request: ResumeRequest):
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

@app.get("/fd/view")
async def view_fd_graph():
    png_bytes = fd_graph.get_graph().draw_mermaid_png()
    return Response(content=png_bytes, media_type="image/png")

@app.post("/fd/start")
async def start_fd(request: StartRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    resume = get_resume_by_email(request.email)
    fd_graph.invoke(
        {"session_id":resume.sessionId},
        config=config
    )
    
    # don't use invoke's return value — get state separately after interrupt
    state = fd_graph.get_state(config)
    
    return {
        "thread_id": thread_id,
        "stage": state.values["current_stage"],
        "question": state.tasks[0].interrupts[0].value["Question"],
        "draft": state.tasks[0].interrupts[0].value["draft"]
    }

@app.post("/fd/resume")
async def resume_fd(request: ResumeRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    
    fd_graph.invoke(
        Command(resume=request.user_data),  # not user_input, resume with answers
        config=config
    )
    
    state = fd_graph.get_state(config)
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