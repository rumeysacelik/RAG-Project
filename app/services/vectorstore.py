import os
import logging
from config.config import settings
from langchain_community.vectorstores import Milvus
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from pymilvus import connections

logger = logging.getLogger(__name__)

def initialize_vectorstore():
    logger.info("Initializing Milvus Vector Store...")
    connections.connect(alias="default", host="localhost", port="19530")
    
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
