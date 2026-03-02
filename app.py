import os
from fastapi import FastAPI, Request
from pinecone import Pinecone
from groq import Groq
import httpx 
import re

# 1. Configuration & Clients
# Use Hugging Face Secrets for these!
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_URL = f"https://149.154.167.220/bot{TELEGRAM_TOKEN}/sendMessage"

EMBED_MODEL= os.environ.get("EMBED_MODEL")
GROQ_MODEL = os.environ.get("GROQ_MODEL")
PROMPT = os.environ.get("PROMPT")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("customerserviceindex")
groq_client = Groq(api_key=GROQ_API_KEY)

app = FastAPI()

def clean_ai_response(text: str):
    # إزالة كل ما بين وسمي <think> و </think> بما في ذلك الوسوم نفسها
    cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned_text.strip()

# 2. The Core AI Logic
async def get_ai_response(user_query: str):
    # Vectorize query using Pinecone Inference
    query_embedding = pc.inference.embed(
        model=EMBED_MODEL,
        inputs=[user_query],
        parameters={"input_type": "query"}
    )

    # Search Pinecone for Bank Context
    search_results = index.query(
        vector=query_embedding[0].values,
        top_k=3,
        include_metadata=True
    )
    
    retrieved_context = "\n".join([res.metadata['original_text'] for res in search_results.matches])

    
    prompt = f"""
    {PROMPT}
    
    Message:{user_query}
    
    Retrieved Context:{retrieved_context}
    
    Final Answer:
    """

    completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=GROQ_MODEL,
        temperature=0.1,
        max_completion_tokens=800,
        top_p=0.9,
    )
    ai_response = completion.choices[0].message.content
    return clean_ai_response(ai_response)

# 3. The Webhook Endpoint
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"].get("text", "")

        if user_text:
            # Get the intelligent response
            ai_answer = await get_ai_response(user_text)
            # Send back to Telegram
            async with httpx.AsyncClient() as client:
                await client.post(
                    TELEGRAM_URL,
                    headers={"Host": "api.telegram.org"},
                    json={
                        "chat_id": chat_id,
                        "text": ai_answer,
                        "parse_mode": "Markdown"
                    }
                )
                
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Hadhramout Bank AI Backend is Live"}

@app.post("/test")
async def test_webhook(request: Request):
    data = await request.json()
    response = await get_ai_response(data["message"]["text"])
    return {"response": response}

import socket

@app.get("/dns-test")
async def dns_test():
    try:
        ip = socket.gethostbyname("api.telegram.org")
        return {"resolved_ip": ip}
    except Exception as e:
        return {"error": str(e)}