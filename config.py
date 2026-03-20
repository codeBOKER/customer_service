import os
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment Variables
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
HF_TOKEN = os.environ.get("HF_TOKEN") or os.environ.get("HF_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


# Only create TELEGRAM_URL if token exists
TELEGRAM_URL = f"https://149.154.167.220/bot{TELEGRAM_TOKEN}/sendMessage" if TELEGRAM_TOKEN else None

EMBED_MODEL = os.environ.get("EMBED_MODEL", "multilingual-e5-large")
HF_MODEL = os.environ.get(
    "HF_MODEL",
    "dphn/Dolphin-Mistral-24B-Venice-Edition",
)
PROMPT = os.environ.get("PROMPT")

# Initialize clients only if API keys are available
pc = None
if PINECONE_API_KEY:
    pc = Pinecone(api_key=PINECONE_API_KEY)

hf_client = None
if HF_TOKEN:
    try:
        hf_client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=HF_TOKEN,
        )
    except Exception as e:
        print(f"Warning: Failed to initialize Hugging Face OpenAI client: {e}")
        hf_client = None

# Initialize index only if Pinecone client is available
index = None
if pc:
    index = pc.Index("customerserviceindex")
