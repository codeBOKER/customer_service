from pydantic import BaseModel
import httpx
import json
from config import TELEGRAM_URL
from ai_service import get_ai_response
from database import db_manager

TELEGRAM_IP = "149.154.167.220"
MAX_TELEGRAM_MESSAGE_LENGTH = 4096


def _sanitize_telegram_text(text: str) -> str:
    if text is None:
        return ""

    normalized = str(text).replace("\r\n", "\n").replace("\r", "\n")

    # Remove control/surrogate chars that Telegram can reject.
    cleaned = "".join(
        ch
        for ch in normalized
        if (ch in ("\n", "\t") or ord(ch) >= 32) and not (0xD800 <= ord(ch) <= 0xDFFF)
    )
    return cleaned.strip()


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
                
                async with httpx.AsyncClient(timeout=40.0, verify=False) as client:
                    prepared_text = _sanitize_telegram_text(
                        ai_answer or "Sorry, I couldn't generate a response. Please try again."
                    )
                    if not prepared_text:
                        prepared_text = "Sorry, I couldn't generate a response. Please try again."

                    final_text = prepared_text[:MAX_TELEGRAM_MESSAGE_LENGTH]
                    payload = {
                        "chat_id": telegram_id,
                        "text": final_text if final_text.strip() else ".",
                    }

                    print(f"--- Sending Telegram message (chars={len(payload['text'])}) ---")

                    try:                        
                        response = await client.post(TELEGRAM_URL, data=payload)
                    except Exception:
                        print(f"--- DNS Failed. Forcing Direct IP Routing to {TELEGRAM_IP} ---")

                        forced_ip_url = f"https://{TELEGRAM_IP}/bot{TELEGRAM_TOKEN}/sendMessage"
                        json_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                        headers = {
                            "Host": "api.telegram.org",
                            "Content-Type": "application/json; charset=utf-8",
                            "Content-Length": str(len(json_body)),
                        }

                        response = await client.post(
                            forced_ip_url,
                            content=json_body,
                            headers=headers,
                        )

                    if response.status_code == 200:
                        print("--- Success: Telegram message delivered ---")
                    else:
                        print("--- Telegram payload rejected ---")
                        print(f"--- Payload: {payload} ---")
                        print(
                            f"--- Telegram Rejected Request: "
                            f"{response.status_code} - {response.text} ---"
                        )
                        
            except Exception as send_error:
                print(f"--- Emergency: Network Blockage Detected: {str(send_error)} ---")
                    
        return {"status": "ok"}
    except Exception as e:
        print(f"Error in webhook: {str(e)}")
        return {"status": "error", "message": str(e)}
