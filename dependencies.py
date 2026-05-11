from langchain_ollama import ChatOllama
from pymongo import MongoClient
from typing import Optional
import logging 

logger = logging.getLogger(__name__)

def ConnectLLM():
    return ChatOllama(base_url="http://localhost:11434",model="nemotron-3-nano:4b")

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
    return get_client().resume_db["resumes"]