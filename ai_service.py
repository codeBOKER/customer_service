import re
from config import pc, index, groq_client, EMBED_MODEL, GROQ_MODEL, PROMPT
from database import db_manager

def clean_ai_response(text: str):
    cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned_text.strip()

async def get_ai_response(user_query: str, telegram_id: int = None):
    
    if not pc or not index or not groq_client:
        return "Ai service is not available at the moment. Please try again later."

    # Save user message if database is available and telegram_id is provided
    if telegram_id and db_manager:
        db_manager.save_message(telegram_id, user_query, "user")

    conversation_history = ""
    if telegram_id and db_manager:
        conversation_history = db_manager.get_formatted_history(telegram_id, limit=6)
    
    
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

    
    user_content = f"""
        ### Historical Conversation:
        {conversation_history}

        ### Retrieved Context from Bank Documents:
        {retrieved_context}

        ### Current User Message:
        {user_query}

        بناءً على ما سبق، قدم إجابة دقيقة ومفيدة للعميل:
        """
    completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": f"{conversation_history}\n\nRetrieved Context: {retrieved_context}\n\nCurrent User Message: {user_query}"}
        ],
        model=GROQ_MODEL,
        temperature=0.1,
        max_completion_tokens=800,
        top_p=0.9,
    )
    ai_response = completion.choices[0].message.content
    cleaned_response = clean_ai_response(ai_response)
    
    # Save assistant response if database is available and telegram_id is provided
    if telegram_id and db_manager:
        db_manager.save_message(telegram_id, cleaned_response, "assistant")
    
    return cleaned_response

