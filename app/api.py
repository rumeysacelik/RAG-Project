from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
from services import setup_retrieval_chain
from model import RequestLog
from db import SessionLocal

import datetime
import json
import logging

app = FastAPI()
router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rag_chain = setup_retrieval_chain()
if not rag_chain:
    raise RuntimeError("Failed to initialize the RAG chain.")

class QueryRequest(BaseModel):
    query: str

@router.post("/search/")
async def search_articles(request: QueryRequest):
    start_time = datetime.datetime.now()
    query = request.query
    chat_history = []

    logger.info(f"Received query: {query}")

    try:
        response = rag_chain.invoke({"input": query, "chat_history": chat_history})

        result = {
            "query": query,
            "answer": response.get("answer", "No answer available")
        }

        # Süreyi Hesaplama
        duration = (datetime.datetime.now() - start_time).total_seconds()

        # Log Kaydı
        with SessionLocal() as db_session:
            log_entry = RequestLog(
                request=json.dumps({"query": query}),
                response=json.dumps(result),
                status_code=200,
                duration=duration,
                log_level="INFO"
            )
            db_session.add(log_entry)
            db_session.commit()

        return result

    except Exception as e:
        logger.error(f"Error during query execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
