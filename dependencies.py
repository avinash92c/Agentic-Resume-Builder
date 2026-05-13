from langchain_ollama import ChatOllama
from pymongo import MongoClient
from typing import Optional
from langgraph.checkpoint.mongodb import MongoDBSaver
import logging 

logger = logging.getLogger(__name__)

def ConnectLLM():
    return ChatOllama(base_url="http://localhost:11434",model="nemotron-3-nano:4b",num_ctx=32768,temperature=0.3)
    

client: Optional[MongoClient] = None

def get_client() -> MongoClient:
    global client
    if client is None:
        client = MongoClient(
            "mongodb://localhost:27017",
            maxPoolSize=10,
            minPoolSize=2,
        )
    return client

def get_collection():
    return get_client().resumebuilder["resumes"]

def load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
    
def get_checkpointer():
    return MongoDBSaver(get_client(),db_name="resumebuilder")