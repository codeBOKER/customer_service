import re
import json
import os
from config import pc, index, EMBED_MODEL, hf_client, PROMPT
from database import db_manager


MODEL_NAME = "dphn/Dolphin-Mistral-24B-Venice-Edition:featherless-ai"

def clean_ai_response(text: str):
    if not text: return ""
    cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned_text.strip()

async def search_bank_knowledge(query: str):
    query_embedding = pc.inference.embed(
        model=EMBED_MODEL,
        inputs=[query],
        parameters={"input_type": "query"}
    )
    
    search_results = index.query(
        vector=query_embedding[0].values,
        top_k=3,
        include_metadata=True
    )
    
    return "\n".join([res.metadata['original_text'] for res in search_results.matches])

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_bank_knowledge",
            "description": "استخدم هذه الأداة للبحث في الملف التعريفي الرسمي لبنك حضرموت للحصول على معلومات دقيقة حول الخدمات، الهيكل التنظيمي، رأس المال، والسياسات.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "جملة البحث باللغة العربية (مثال: 'ما هو رأس مال بنك حضرموت؟' أو 'خدمات الأفراد')."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

async def get_ai_response(user_query: str, telegram_id: int):
    conversation_history = []
    if db_manager:
        raw_history = db_manager.get_conversation_history(telegram_id, limit=6)
        for msg in raw_history:            
            if msg.get('content'):
                conversation_history.append({"role": msg['role'], "content": msg['content']})

    messages = [{"role": "system", "content": PROMPT}] + conversation_history
    
    
    import asyncio
    loop = asyncio.get_event_loop()
    
    
    def call_hf():
        return hf_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.1,
            max_tokens=800
        )
    
    completion = await loop.run_in_executor(None, call_hf)
    return clean_ai_response(completion.choices[0].message.content)