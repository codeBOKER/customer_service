import socket

async def dns_test():
    try:
        ip = socket.gethostbyname("api.telegram.org")
        return {"resolved_ip": ip}
    except Exception as e:
        return {"error": str(e)}

async def test_ai_response(message: str, telegram_id: int):
    try:
        from ai_service import get_ai_response
        response = await get_ai_response(message, telegram_id)
        return {
            "message": message,
            "telegram_id": telegram_id,
            "response": response,
        }
    except Exception as e:
        return {"error": str(e)}
