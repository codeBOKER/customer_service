import os
from pinecone import Pinecone
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment Variables
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


# Only create TELEGRAM_URL if token exists
TELEGRAM_URL = f"https://149.154.167.220/bot{TELEGRAM_TOKEN}/sendMessage" if TELEGRAM_TOKEN else None

EMBED_MODEL = os.environ.get("EMBED_MODEL", "multilingual-e5-large")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
PROMPT = os.environ.get("PROMPT", "You are a helpful customer service assistant for Hadhramout Bank. Answer the user's question based on the provided context. If the context doesn't contain the answer, politely say you don't have enough information to help with that specific query.")

# Initialize clients only if API keys are available
pc = None
if PINECONE_API_KEY:
    pc = Pinecone(api_key=PINECONE_API_KEY)

groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Warning: Failed to initialize Groq client: {e}")
        groq_client = None

# Initialize index only if Pinecone client is available
index = None
if pc:
    index = pc.Index("customerserviceindex")
