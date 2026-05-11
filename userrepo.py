from dependencies import get_collection
from pymongo.errors import PyMongoError
import logging

logger = logging.getLogger(__name__)

def save_section(session_id: str, section: str, data: dict):
    try:
        col = get_collection()
        col.update_one(
            {"session_id": session_id},
            {"$set": {section: data}},
            upsert=True
        )
    except PyMongoError as e:
        logger.error("Failed to save section {} for session {}: {}", section, session_id, e)
        raise

def get_resume(session_id: str):
    try:
        col = get_collection()
        return col.find_one({"session_id": session_id})
    except PyMongoError as e:
        logger.error("Failed to Read document {}: {}", session_id, e)
        raise