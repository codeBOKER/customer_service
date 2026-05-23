import httpx
import json
import html
import re
import asyncio
from config import TELEGRAM_URL, TELEGRAM_TOKEN
from ai_service import get_ai_response
from database import db_manager
from schemas import WebhookData

TELEGRAM_IP = "149.154.167.220"
MAX_TELEGRAM_MESSAGE_LENGTH = 4096

def _sanitize_telegram_text(text: str) -> str:
    if text is None:
        return ""
    normalized = str(text).replace("\r\n", "\n").replace("\r", "\n")
    cleaned = "".join(
        ch
        for ch in normalized
        if (ch in ("\n", "\t") or ord(ch) >= 32) and not (0xD800 <= ord(ch) <= 0xDFFF)
    )
    return cleaned.strip()

def _format_telegram_message(text: str) -> str:
    if not text:
        return text
    escaped = html.escape(text, quote=False)
    formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', escaped)
    return formatted

async def telegram_webhook(data: WebhookData):
    try:
        if not data.message or not data.message.text:
            return {"status": "ok"}

        telegram_id = data.message.chat.id
        user_text = data.message.text
        username = data.message.chat.username
        first_name = data.message.chat.first_name

        # 1. تحديث المستخدم (Async)
        if db_manager:
            await db_manager.create_or_update_user(telegram_id, username, first_name, data.message.chat.last_name)

        # 2. الحصول على رد الـ AI
        ai_answer = await get_ai_response(user_text, telegram_id)
        final_response = ai_answer or "Sorry, I couldn't generate a response."

        # 3. إرسال الرسالة باستخدام IP مباشر لتجنب تأخير DNS
        if TELEGRAM_TOKEN:
            async with httpx.AsyncClient(timeout=40.0, verify=False) as client:
                prepared_text = _sanitize_telegram_text(final_response)
                formatted_text = _format_telegram_message(prepared_text)
                final_text = formatted_text[:MAX_TELEGRAM_MESSAGE_LENGTH]
                
                payload = {
                    "chat_id": telegram_id,
                    "text": final_text if final_text.strip() else ".",
                    "parse_mode": "HTML",
                }

                # رابط مباشر لتجاوز DNS
                forced_ip_url = f"https://{TELEGRAM_IP}/bot{TELEGRAM_TOKEN}/sendMessage"
                headers = {
                    "Host": "api.telegram.org",
                    "Content-Type": "application/json; charset=utf-8",
                }

                response = await client.post(forced_ip_url, json=payload, headers=headers)

                if response.status_code == 200:
                    print("--- Success: Telegram message delivered ---")
                    # 4. حفظ المحادثة بعد التأكد من وصول الرسالة
                    if db_manager:
                        await asyncio.gather(
                            db_manager.save_message(telegram_id, user_text, "user"),
                            db_manager.save_message(telegram_id, final_response, "assistant")
                        )
                else:
                    print(f"--- Telegram Rejected: {response.status_code} - {response.text} ---")
        
        return {"status": "ok"}
    except Exception as e:
        print(f"Error in webhook: {str(e)}")
        return {"status": "error", "message": str(e)}