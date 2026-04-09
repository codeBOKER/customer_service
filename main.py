from fastapi import FastAPI, Header, Request
from security import validate_webhook_secret
from telegram_handlers import telegram_webhook, WebhookData
from utils import dns_test, test_ai_response

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hadhramout Bank AI Backend is Live"}

@app.post("/webhook")
async def webhook(
    request: Request,
    data: WebhookData,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    validate_webhook_secret(request, x_telegram_bot_api_secret_token)

    return await telegram_webhook(data)

@app.get("/dns-test")
async def dns(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    validate_webhook_secret(request, x_telegram_bot_api_secret_token)
    return await dns_test()

@app.get("/ai-test")
async def ai(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    validate_webhook_secret(request, x_telegram_bot_api_secret_token)
    return await test_ai_response()
