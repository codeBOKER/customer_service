from fastapi import Request
from pydantic import BaseModel
import httpx
from config import TELEGRAM_URL
from ai_service import get_ai_response
from database import db_manager

TELEGRAM_IP = "149.154.167.220"

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
        if not data.message or not data.message.text:
            return {"status": "ok"}

        telegram_id = data.message.chat.id
        user_text = data.message.text
        
        username = data.message.chat.username
        first_name = data.message.chat.first_name

        print(f"--- Processing message from {first_name} ---")

        if db_manager:
            db_manager.create_or_update_user(telegram_id, username, first_name, data.message.chat.last_name)

        
        ai_answer = await get_ai_response(user_text, telegram_id)
        

        
        if TELEGRAM_URL:
            try:
                from config import TELEGRAM_TOKEN 
                
                async with httpx.AsyncClient(timeout=40.0, verify=False, follow_redirects=True) as client:
                    # 1. Clean the input
                    clean_answer = str(ai_answer).strip() if ai_answer else ""
                    
                    # 2. Ensure it's not empty
                    if not clean_answer:
                        clean_answer = "Default fallback: The AI returned an empty result."

                    payload = {
                        "chat_id": telegram_id,
                        "text": clean_answer
                    }
                    
                    # 3. Explicitly log the type and content
                    print(f"DEBUG: ai_answer type: {type(ai_answer)}")
                    print(f"DEBUG: Sending Payload: {payload}")

                    try:
                        # Try standard URL first
                        response = await client.post(TELEGRAM_URL, json=payload)
                    except Exception as dns_err:
                        print(f"--- DNS Failed. Routing to IP ---")
                        forced_ip_url = f"https://149.154.167.220/bot{TELEGRAM_TOKEN}/sendMessage"
                        headers = {"Host": "api.telegram.org"}
                        # Use 'json=' to ensure httpx sets the correct Content-Type automatically
                        response = await client.post(forced_ip_url, json=payload, headers=headers)
                        
            except Exception as send_error:
                print(f"--- Emergency: Network Blockage Detected: {str(send_error)} ---")
                    
        return {"status": "ok"}
    except Exception as e:
        print(f"Error in webhook: {str(e)}")
        return {"status": "error", "message": str(e)}