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
        if not data.message or not data.message.text:
            return {"status": "ok"}

        telegram_id = data.message.chat.id
        user_text = data.message.text
        
        # معلومات المستخدم
        username = data.message.chat.username
        first_name = data.message.chat.first_name

        print(f"--- Processing message from {first_name} ---")

        # 1. تحديث بيانات المستخدم وحفظ رسالته (مرة واحدة فقط هنا)
        if db_manager:
            db_manager.create_or_update_user(telegram_id, username, first_name, data.message.chat.last_name)
            db_manager.save_message(telegram_id, user_text, "user")
        
        # 2. جلب الرد (تأكد من إزالة حفظ الرسالة المتكرر داخل get_ai_response)
        ai_answer = await get_ai_response(user_text, telegram_id)
        
        # 3. حفظ رد البوت
        if db_manager:
            db_manager.save_message(telegram_id, ai_answer, "assistant")
        
        # 4. الإرسال لتليجرام (تم تنظيفه من الهيدرز الزائدة)
        if TELEGRAM_URL:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "chat_id": telegram_id,
                    "text": ai_answer,
                    "parse_mode": "Markdown"
                }
                # حذفنا Host Header و verify=False (إلا لو كنت متأكداً من حاجتك لها)
                response = await client.post(TELEGRAM_URL, json=payload)
                print(f"Telegram response status: {response.status_code}")
                    
        return {"status": "ok"}
    except Exception as e:
        print(f"Error in webhook: {str(e)}")
        return {"status": "error", "message": str(e)}