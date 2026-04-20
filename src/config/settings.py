import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "chatbot_db")
DB_PORT = int(os.getenv("DB_PORT", 3306))

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "products")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


class ModelType:
    gpt4o = "gpt-4o"
    gpt4o_mini = "gpt-4o-mini"
