import re
import json
import os
from config import pc, index, EMBED_MODEL, hf_client, PROMPT
from database import db_manager


MODEL_NAME = "dolphin-mistral-24b-venice-edition"

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

# تعريف الأداة (Tool) الخاصة بالبحث في وثائق البنك
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

async def get_ai_response(user_query: str, telegram_id: int = None):
    if not pc or not index or not hf_client:
        return "عذراً، خدمة الذكاء الاصطناعي غير متوفرة حالياً."

    print(f"User query: {user_query}")
    conversation_history = []
    if telegram_id and db_manager:
        db_manager.save_message(telegram_id, user_query, "user")
        # جلب آخر 6 رسائل لتوفير السياق للموديل
        raw_history = db_manager.get_history(telegram_id, limit=6)
        for msg in raw_history:
            conversation_history.append({"role": msg['role'], "content": msg['content']})
    else:
        conversation_history.append({"role": "user", "content": user_query})

    
    messages = [{"role": "system", "content": PROMPT}] + conversation_history

    print(f"getting response from Messages: {messages}")
    response = hf_client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.1 
    )

    response_message = response.choices[0].message
    tool_calls = getattr(response_message, 'tool_calls', None)

    
    if tool_calls:
        print(f"tool_calls: {tool_calls}")
        for tool_call in tool_calls:
            function_args = json.loads(tool_call.function.arguments)
            search_query = function_args.get("query")
            
            
            extracted_context = await search_bank_knowledge(search_query)
            
            
            messages.append(response_message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": "search_bank_knowledge",
                "content": extracted_context
            })

        
        final_response = hf_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.3
        )
        ai_final_content = final_response.choices[0].message.content
    else:
        print(f"response_message: {response_message}")
        ai_final_content = response_message.content

    print(f"ai_final_content: {ai_final_content}")
    cleaned_response = clean_ai_response(ai_final_content)
    
    if telegram_id and db_manager:
        db_manager.save_message(telegram_id, cleaned_response, "assistant")
    
    return cleaned_response