import os
import logging
from config import settings
from langchain_community.vectorstores import Milvus
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from pymilvus import connections, utility
from prompts import contextualize_q_prompt, qa_prompt
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chains.combine_documents import create_stuff_documents_chain


logger = logging.getLogger(__name__)

def initialize_vectorstore():
    logger.info("Initializing Milvus Vector Store...")
    
    connections.connect(alias="default", host="localhost", port="19530")
    # embeddings = AzureOpenAIEmbeddings(
    #     model="text-embedding-ada-002",
    #     openai_api_key=settings.OPENAI_API_KEY
    # )
    embeddings = AzureOpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_key=settings.OPENAI_API_KEY,
        azure_endpoint="https://softtech-openaitest.openai.azure.com"
    )
    

    if not os.path.exists(settings.FILEPATH):
        raise FileNotFoundError(f"PDF file not found: {settings.FILEPATH}")
    
    logger.info("Loading PDF...")
    loader = PyPDFLoader(settings.FILEPATH)
    documents = loader.load()
    logger.info(f"Loaded {len(documents)} pages from PDF.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        length_function=len
    )
    docs = text_splitter.split_documents(documents)
    logger.info(f"Split documents into {len(docs)} chunks.")

    vectorstore = Milvus.from_documents(
        docs,
        embeddings,
        connection_args={"uri": settings.MILVUS_URI},
        collection_name=settings.COLLECTION_NAME,
        index_params={"metric_type": "IP"}
    )
    logger.info("Milvus Vector Store initialization complete.")
    return vectorstore


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
    print("Collections in Milvus:", collections)


    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    
    # Yeni document chain oluşturma yöntemi
    document_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=qa_prompt
    )
    
    return create_retrieval_chain(history_aware_retriever, document_chain)