import logging
from langchain_openai import AzureChatOpenAI
from pymilvus import utility
from models.schemas.prompts import contextualize_q_prompt, qa_prompt
from services.vectorstore import initialize_vectorstore
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from config.config import settings


logger = logging.getLogger(__name__)

def setup_retrieval_chain():
    db = initialize_vectorstore()
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 5, "score_threshold": 0.7})

    llm = AzureChatOpenAI(
        model="gpt-4o",
        openai_api_key=settings.OPENAI_API_KEY,
        azure_endpoint="https://softtech-openaitest.openai.azure.com",
        api_version="2024-04-01-preview"
    )
    collections = utility.list_collections()
    logger.info(f"Collections in Milvus: {collections}")

    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

    document_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=qa_prompt
    )
    
    return create_retrieval_chain(history_aware_retriever, document_chain)
