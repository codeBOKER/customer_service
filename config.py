import os
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment Variables
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX = os.environ.get("PINECONE_INDEX", "customerserviceindex")
HF_TOKEN = os.environ.get("HF_TOKEN") or os.environ.get("HF_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TELEGRAM_DOMAIN = os.environ.get("TELEGRAM_DOMAIN", "https://api.telegram.org").rstrip("/")

# Only create TELEGRAM_URL if token exists
TELEGRAM_URL = f"{TELEGRAM_DOMAIN}/bot{TELEGRAM_TOKEN}/sendMessage" if TELEGRAM_TOKEN and TELEGRAM_DOMAIN else None

EMBED_MODEL = os.environ.get("EMBED_MODEL", "multilingual-e5-large")
HF_MODEL = os.environ.get(
    "HF_MODEL",
    "dphn/Dolphin-Mistral-24B-Venice-Edition",
)
PROMPT = os.environ.get("PROMPT")
TRANSFER_PROMPT = os.environ.get("TRANSFER_PROMPT")

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
    index = pc.Index(PINECONE_INDEX)
