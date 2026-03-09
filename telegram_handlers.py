from fastapi import Request
import httpx
from config import TELEGRAM_URL
from ai_service import get_ai_response
from database import db_manager

async def telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" in data:
        telegram_id = data["message"]["chat"]["id"]
        user_text = data["message"].get("text", "")
        
        # Extract user info
        user_info = data["message"]["chat"]
        username = user_info.get("username")
        first_name = user_info.get("first_name")
        last_name = user_info.get("last_name")

        if user_text:
            # Save user message to database if available
            if db_manager:
                db_manager.save_message(telegram_id, user_text, "user")
                db_manager.create_or_update_user(telegram_id, username, first_name, last_name)
            
            # Get the intelligent response with conversation history
            ai_answer = await get_ai_response(user_text, telegram_id)
            
            # Save assistant response to database if available
            if db_manager:
                db_manager.save_message(telegram_id, ai_answer, "assistant")
            
            # Send back to Telegram if TELEGRAM_URL is available
            if TELEGRAM_URL:
                async with httpx.AsyncClient(verify=False) as client:
                    await client.post(
                        TELEGRAM_URL,
                        headers={"Host": "api.telegram.org"},
                        json={
                            "chat_id": telegram_id,
                            "text": ai_answer,
                            "parse_mode": "Markdown"
                        }
                    )
                
    return {"status": "ok"}

async def test_webhook(request: Request):
    data = await request.json()
    telegram_id = data["message"]["chat"]["id"]
    user_text = data["message"]["text"]
    
    # Save user message to database if available
    if db_manager:
        db_manager.save_message(telegram_id, user_text, "user")
    
    # Get response with conversation history
    response = await get_ai_response(user_text, telegram_id)
    
    # Save assistant response to database if available
    if db_manager:
        db_manager.save_message(telegram_id, response, "assistant")
    
    return {"response": response}
