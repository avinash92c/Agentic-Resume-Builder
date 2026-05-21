from fastapi import FastAPI,HTTPException,Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from model import CertificationsRequest, EducationInfoRequest, PersonalInfo,Education,Certifications,StartRequest,ResumeRequest
from userrepo import save_section,get_resume_by_email
import uuid
from typing import List,Dict, Any
from pymongo.errors import PyMongoError
from agent_psg import PSG_GRAPH
from agent_wh import WH_GRAPH
from agent_pp import PP_GRAPH
from agent_final import FINAL_GRAPH
from langgraph.types import Command
from model import AgentResponse, AgentResponseData
from responsebuilder import map_interrupt_data
from SkillFlow.agent_skill import skills_app 
from fastapi import FastAPI, HTTPException

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

appTwo = FastAPI(title="Agentic Resume Builder Interviewer")

class StartInterviewRequest(BaseModel):
    session_id: str
    raw_skills_input: str

class UserReplyRequest(BaseModel):
    session_id: str
    user_answer: str

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
async def start_wh(request: StartRequest):
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

@app.get("/skills/view")
async def view_skills_graph():
    png_bytes = skills_app.get_graph().draw_mermaid_png()
    return Response(content=png_bytes, media_type="image/png")

from pydantic import BaseModel

class RefineRequest(BaseModel):
    thread_id: str
    refinement: str
    approved: bool = False

@app.post("/skills/start")
async def start_skills(request: StartRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    resume = get_resume_by_email(request.email)
    if resume is None:
        raise HTTPException(status_code=404, detail=f"No resume found for email: {request.email}")
    
    skills_app.invoke(
        {
            "raw_skills_input": request.user_input,
            "session_id": resume.sessionId,
            "drafts": [],
            "refinements": [],
            "approved": False,
            "refinement_counts": 0,
            "current_stage": "starting"
        },
        config=config
    )
    
    state = skills_app.get_state(config)
    is_interrupted = bool(state.tasks)

    return {
        "thread_id": thread_id,
        "stage": state.values["current_stage"],
        "current_draft": state.values["drafts"][-1] if state.values.get("drafts") else None,
        "refinement_question": state.tasks[0].interrupts[0].value["message"] if is_interrupted else None,
        "complete": not is_interrupted
    }


@app.post("/skills/resume")
async def resume_skills(request: RefineRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    
    skills_app.invoke(
        Command(resume={"refinement": request.refinement, "approved": request.approved}),
        config=config
    )
    
    state = skills_app.get_state(config)
    is_interrupted = bool(state.tasks)

    return {
        "thread_id": request.thread_id,
        "stage": state.values["current_stage"],
        "current_draft": state.values["drafts"][-1] if state.values.get("drafts") else None,
        "refinement_question": state.tasks[0].interrupts[0].value["message"] if is_interrupted else None,
        "complete": not is_interrupted
    }

@app.post("/interview/start")
async def start_interview(payload: StartInterviewRequest):
    """Initializes the graph runtime state and generates the 5 core questions."""
    config = {"configurable": {"thread_id": payload.session_id}}
    
    initial_state = {
        "raw_skills_input": payload.raw_skills_input,
        "generated_questions": [
            "What was the percentage increase in request processing speed after implementing your FastAPI solution?",
            "Which specific tools or frameworks beyond FastAPI and LangGraph did you use?",
            "Did you personally design and deploy the LangGraph workflow?"
        ], 
        "user_answers": {},
        "current_question_index": 0,
        "current_stage": "starting"
    }
     # Collect all events into a list first
    all_events = list(skills_app.stream(initial_state, config, stream_mode="values"))
    
    state_snapshot = skills_app.get_state(config)
    
    if state_snapshot.next:
        return {
            "status": "paused",
            "turn_data": state_snapshot.tasks[0].interrupts[0].value
        }
    
    # # Run the graph until it encounters the first single-question interrupt
    # events = skills_app.stream(initial_state, config, stream_mode="values")
    
    # for event in events:
    #     if "Skills_ChatInterviewer" in event:
    #         state_snapshot = skills_app.get_state(config)
    #         if state_snapshot.next: # Verifies graph is currently paused at interrupt
    #             return {"status": "paused", "turn_data": state_snapshot.next[0].value}
                
    return {"status": "completed", "final_state": all_events[-1] if all_events else {}}




@app.post("/interview/reply")
async def register_reply(payload: UserReplyRequest):
    """Resumes the graph thread execution state by injecting the specific turn input."""
    config = {"configurable": {"thread_id": payload.session_id}}
    
    # 🚀 Inject user feedback answer directly to kick off the interrupt block
    events = skills_app.stream(
        Command(resume={"answer": payload.user_answer}), 
        config, 
        stream_mode="values"
    )
    
    state_snapshot = skills_app.get_state(config)
    
    # If the state graph hit another interrupt checkpoint, yield the next item in the queue
    if state_snapshot.next:
        return {
            "status": "paused", 
            # "turn_data": state_snapshot.next[0].value
             "turn_data": state_snapshot.tasks[0].interrupts[0].value
        }
        
    return {
        "status": "interview_session_complete", 
        "message": "All answers securely saved to Data Lake."
    }
