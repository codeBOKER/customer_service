from fastapi import Request
from pydantic import BaseModel
import httpx
from config import TELEGRAM_URL
from ai_service import get_ai_response
from database import db_manager

class ChatInfo(BaseModel):
    id: int
    username: str = None
    first_name: str = None
    last_name: str = None

class Message(BaseModel):
    chat: ChatInfo
    text: str = ""

class WebhookData(BaseModel):
    message: Message = None

async def telegram_webhook(data: WebhookData):
    try:
        if data.message:
            telegram_id = data.message.chat.id
            user_text = data.message.text
            
            # Extract user info
            username = data.message.chat.username
            first_name = data.message.chat.first_name
            last_name = data.message.chat.last_name

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
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def test_webhook(data: WebhookData):
    try:
        if not data.message:
            return {"error": "Missing 'message' field in request"}
            
        telegram_id = data.message.chat.id
        user_text = data.message.text
        
        # Save user message to database if available
        if db_manager:
            db_manager.save_message(telegram_id, user_text, "user")
        
        # Get response with conversation history
        response = await get_ai_response(user_text, telegram_id)
        
        # Save assistant response to database if available
        if db_manager:
            db_manager.save_message(telegram_id, response, "assistant")
        
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}
