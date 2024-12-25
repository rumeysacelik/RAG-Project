import os
import textwrap
import logging
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Milvus
# from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from pymilvus import connections, utility
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from fastapi import Request
import time
from starlette.responses import Response
import json


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# load_dotenv()
DATABASE_URL=""
openai_api_key = ""


Base = declarative_base()

# log table  model
#embeddingVectorize - database
class RequestLog(Base):
    __tablename__ = 'request_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    request = Column(String, nullable=False)  
    response = Column(String, nullable=False) 
    status_code = Column(Integer, nullable=False) 
    duration = Column(Float, nullable=False)  
    log_level = Column(String, nullable=False)  
    created_date = Column(DateTime, default=datetime.datetime.utcnow) 

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tabloları oluştur
Base.metadata.create_all(bind=engine)


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
FILEPATH = os.path.abspath("druglistt.pdf")

MILVUS_URI = "http://localhost:19530"
COLLECTION_NAME = "drug_collection2"

def initialize_vectorstore():
    logger.info("Initializing Milvus Vector Store...")
    
    logger.info("Connecting to Milvus server...")
    connections.connect(alias="default", host="localhost", port="19530")

    embeddings = AzureOpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=openai_api_key,
            azure_endpoint="https://softtech-openaitest.openai.azure.com"
    )

    

    if not os.path.exists(FILEPATH):
        logger.error(f"PDF file not found: {FILEPATH}")
        raise FileNotFoundError(f"PDF file not found: {FILEPATH}")

    logger.info("Loading PDF...")
    loader = PyPDFLoader(FILEPATH)
    documents = loader.load()
    logger.info(f"Loaded {len(documents)} pages from PDF.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, 
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len
    )
    docs = text_splitter.split_documents(documents)

    logger.info(f"Split documents into {len(docs)} chunks.")
    # for doc in docs:
    #     print(f"Chunk length: {len(doc.page_content)} characters")
    # Milvus koleksiyonu oluşturma veya var olanı kullanma
    logger.info(f"Creating/updating Milvus collection: {COLLECTION_NAME}")
    vectorstore = Milvus.from_documents(
        docs,
        embeddings,
        connection_args={"uri": MILVUS_URI},
        collection_name=COLLECTION_NAME,
        index_params={"metric_type": "IP"}  # İç çarpım (IP) metriği
    )
    logger.info("Milvus Vector Store initialization complete.")
    return vectorstore

try:
    db = initialize_vectorstore()
except Exception as e:
    logger.error("Failed to initialize Milvus Vector Store: %s", e)
    raise e

collections = utility.list_collections()
print("Collections in Milvus:", collections)

retriever = db.as_retriever(
    search_type="similarity", 
    search_kwargs={"k": 5, "score_threshold": 0.7}
)


llm = AzureChatOpenAI(
    model="gpt-4o", 
    openai_api_key=openai_api_key,
    azure_endpoint="https://softtech-openaitest.openai.azure.com",
    api_version="2024-04-01-preview"
)

# llm = AzureChatOpenAI(
#     deployment=AZURE_DEPLOYMENT_NAME,
#     model=AZURE_MODEL_NAME,
#     api_key=AZURE_OPENAI_API_KEY,
#     api_base=AZURE_OPENAI_ENDPOINT,
#     api_version=AZURE_OPENAI_API_VERSION
# )



#nedenler?
#neden textsplitter olarak bunu kullandık da neden diğerlerini kullanmadık.bunun avantajı ne?
#neden cosin kullanılır - benzer veriler varsa hep bir yerde toplanmışsa veriler kullanırız - mmr neden kullanılır - hangi senaryoda ahngisini tercih ediyoruz
#farkı ne
contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", "Rephrase the question based on context, ensuring it is standalone."),
    
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", "Use the following context to answer the query: {context}"),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     start_time = time.time()
#     request_body = await request.body()
#     request_body_decoded = request_body.decode("utf-8") if request_body else ""

#     response = await call_next(request)

#     duration = time.time() - start_time

#     # Yanıt gövdesi
#     response_body = b"".join([chunk async for chunk in response.body_iterator]).decode("utf-8")

#     log_level = "INFO"
#     status_code = response.status_code

#     with SessionLocal() as db:
#         log_entry = RequestLog(
#             request=request_body_decoded,
#             response=response_body,
#             status_code=status_code,
#             duration=duration,
#             log_level=log_level
#         )
#         db.add(log_entry)
#         db.commit()

#     new_response = Response(
#         content=response_body,
#         status_code=response.status_code,
#         headers=dict(response.headers),
#         media_type=response.media_type
#     )
#     return new_response

class QueryRequest(BaseModel):
    query: str
    # top_k: int = 3

@app.get("/logs")
def get_logs():
    with SessionLocal() as db:
        logs = db.query(RequestLog).all()
        return logs

@app.get("/")
async def root():
    return {"message": "Welcome to the Drug Search API. Use POST /search/ to query the API."}

# @app.post("/search/")
# async def search_articles(request: QueryRequest):
#     query = request.query
#     logger.info(f"Received query: {query}")
#     chat_history = []

#     try:
#         response = rag_chain.invoke({"input": query, "chat_history": chat_history})
#         return {"query": query, "answer": textwrap.fill(response["answer"], width=88)}
#     except Exception as e:
#         logger.error("Error during query execution: %s", e)
#         return {"error": str(e)}

@app.get("")
def get_logs():
    with SessionLocal() as db:
        logs = db.query(RequestLog).all()
        return logs
    
@app.post("/search/")
async def search_articles(request: QueryRequest):
    start_time = datetime.datetime.now()
    query = request.query
    top_k = 5

    logger.info(f"Received query: {query}")
    chat_history = []

    try:
        dynamic_retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": top_k})
        history_aware_retriever = create_history_aware_retriever(llm, dynamic_retriever, contextualize_q_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        response = rag_chain.invoke({"input": query, "chat_history": chat_history})
        
        result = {
            "query": query,
            "answer": textwrap.fill(response["answer"], width=88)
        }

        # Calculate duration
        duration = (datetime.datetime.now() - start_time).total_seconds()

        # Log the request
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
        logger.error("Error during query execution: %s", e)
        duration = (datetime.datetime.now() - start_time).total_seconds()
        
        error_response = {"error": str(e)}
        
        with SessionLocal() as db_session:
            log_entry = RequestLog(
                request=json.dumps({"query": query}),
                response=json.dumps(error_response),
                status_code=500,
                duration=duration,
                log_level="ERROR"
            )
            db_session.add(log_entry)
            db_session.commit()

        return error_response

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server on http://localhost:8000...")
    uvicorn.run(app, host="localhost", port=8000)
