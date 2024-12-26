import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "DATABASE_URL")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "OPENAI_API_KEY")
    MILVUS_URI = os.getenv("MILVUS_URI", "http://localhost:19530")
    FILEPATH = os.getenv("FILEPATH", os.path.abspath("druglistt.pdf"))
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    COLLECTION_NAME = "drug_collection2"

settings = Settings()


