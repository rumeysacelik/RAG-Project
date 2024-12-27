from fastapi import APIRouter, HTTPException
from models.model import RequestLog
from config.db import SessionLocal

import json
import logging

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/history/")
async def get_chat_history(limit: int = 10):

    try:
        with SessionLocal() as db_session:
            logs = db_session.query(RequestLog).order_by(RequestLog.created_date.desc()).limit(limit).all()
            history = [
                {
                    "id": log.id,
                    "request": json.loads(log.request),
                    "response": json.loads(log.response),
                    "status_code": log.status_code,
                    "duration": log.duration,
                    "created_date": log.created_date
                }
                for log in logs
            ]
        return {"history": history}
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat history")
