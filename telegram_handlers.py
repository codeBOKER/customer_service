from fastapi import Request
from pydantic import BaseModel
import httpx
import json
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
                    payload = {
                        "chat_id": telegram_id,
                        "text": ai_answer or "Sorry, I couldn't generate a response. Please try again."
                    }
                    
                    print(f"--- Payload being sent: {payload} ---")
                    
                    try:
                        # Attempt standard request
                        response = await client.post(TELEGRAM_URL, json=payload)
                    except Exception as dns_err:
                        print(f"--- DNS Failed. Forcing Direct IP Routing to 149.154.167.220 ---")

                        forced_ip_url = f"https://{TELEGRAM_IP}/bot{TELEGRAM_TOKEN}/sendMessage"

                        # 1. Manually dump to JSON string to ensure UTF-8 for Arabic
                        json_body = json.dumps(payload, ensure_ascii=False).encode('utf-8')

                        headers = {
                            "Host": "api.telegram.org",
                            "Content-Type": "application/json",
                            "Content-Length": str(len(json_body)) # Explicitly tell Telegram the size
                        }

                        # 2. Use 'content=' or 'data=' instead of 'json='
                        response = await client.post(
                            forced_ip_url, 
                            content=json_body, 
                            headers=headers
                        )
                    
                    if response.status_code == 200:
                        print(f"--- Success: Message delivered via Direct IP Pipeline ---")
                    else:
                        print(f"--- Payload: {payload} ---")
                        print(f"--- Telegram Rejected Request: {response.status_code} - {response.text} ---")
                        
            except Exception as send_error:
                print(f"--- Emergency: Network Blockage Detected: {str(send_error)} ---")
                    
        return {"status": "ok"}
    except Exception as e:
        print(f"Error in webhook: {str(e)}")
        return {"status": "error", "message": str(e)}