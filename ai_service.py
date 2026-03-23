import re
import json
import os
from config import pc, index, EMBED_MODEL, hf_client, PROMPT, HF_MODEL
from database import db_manager


MODEL_NAME = HF_MODEL

def clean_ai_response(text: str):
    if not text: return ""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Remove markdown tables
    text = re.sub(r'\|.*?\|', '', text)
    text = re.sub(r'[-|]{3,}', '', text)
    # Remove HTML tags
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    # Remove markdown bold/italic
    text = re.sub(r'[*_]{1,3}(.*?)[*_]{1,3}', r'\1', text)
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # Clean up extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

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
            "description": "Use this tool to search the official Hadhramout Bank profile for accurate information about services, organizational structure, capital, and policies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g., 'What is Hadhramout Bank capital?' or 'individual services')."
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
        raw_history.reverse()
        for msg in raw_history:
            if msg.get('message_text'):
                role = "user" if msg['message_type'] == 'user' else "assistant"
                conversation_history.append({"role": role, "content": msg['message_text']})

    messages = [{"role": "system", "content": PROMPT}] + conversation_history + [{"role": "user", "content": user_query}]
    
    
    import asyncio
    loop = asyncio.get_event_loop()
    
    
    def call_hf(msgs):
        return hf_client.chat.completions.create(
            model=MODEL_NAME,
            messages=msgs,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.1,
            max_tokens=800
        )

    completion = await loop.run_in_executor(None, lambda: call_hf(messages))
    response_message = completion.choices[0].message

    # Handle tool call if model requests it
    if response_message.tool_calls:
        tool_call = response_message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        tool_result = await search_bank_knowledge(args["query"])

        messages.append(response_message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": tool_result
        })

        completion = await loop.run_in_executor(None, lambda: call_hf(messages))
        response_message = completion.choices[0].message

    final_response = clean_ai_response(response_message.content)

    if db_manager:
        db_manager.save_message(telegram_id, user_query, "user")
        db_manager.save_message(telegram_id, final_response, "assistant")

    return final_response