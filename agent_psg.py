import logging
from typing import List,TypedDict
from dependencies import ConnectLLM,load_prompt
from langchain.messages import SystemMessage,HumanMessage
from langgraph.graph import START,END,StateGraph,MessagesState

logger = logging.getLogger(__name__) # GET LOGGER

llm = ConnectLLM()

class ProfessionalSummaryState(MessagesState):
    user_input_initial:str
    refinement_counts:int
    generated_questions:List[str]
    user_answers:dict[str,str]
    refinements:List[str]
    drafts:List[str] #WILL CONTAIN ALL THREE DRAFT VERSIONS IN SEQUENCE. LAST DRAFT WILL BE THE FINAL DRAFT
    approved: bool
    current_stage: str
    
class GeneratedQuestionsResult(TypedDict):
    questions:List[str]
    
professional_summary_graph = StateGraph(ProfessionalSummaryState)

# THIS GRAPH GETS INVOKED BY UI WITH USER INPUT
# PREPAGE QUESTIONS TAKES THAT INPUT AND CALLS LLM AND PRESENTS USER WITH 5/10 QUESTIONS FOR REFINEMENT 1st ROUND
# GRAPH SHOULD PAUSE FOR USER INPUTS

def PSG_PrepareQuestions(state:ProfessionalSummaryState):
    system_prompt = load_prompt("prompts\PSG\prepare_questions.txt")
    llm_messages = [
        SystemMessage(system_prompt),
        HumanMessage(state.user_input_initial)
    ]
    result = llm.with_structured_output(GeneratedQuestionsResult).invoke(llm_messages)
    logging.debug("PSG_PrepareQuestions result {}",result)
    
    return {
    # "messages": [result], # TEST AND ENSURE THIS IS PROPERLY HANDLED
    "generated_questions": result.questions
    }

def PSG_PrepareForIntialDraft(messages:MessagesState):
    pass

def PSG_PresentForReview(messages:MessagesState):
    pass

def PSG_NeedRefinement(messages:MessagesState):
    pass

def PSG_AskInputs(messages:MessagesState):
    pass

def PSG_StoreDB(messages:MessagesState):
    pass