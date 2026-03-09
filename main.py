from fastapi import FastAPI
from telegram_handlers import telegram_webhook, test_webhook
from utils import dns_test, test_ai_response

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hadhramout Bank AI Backend is Live"}

@app.post("/webhook")
async def webhook(request):
    return await telegram_webhook(request)

@app.post("/test")
async def test(request):
    return await test_webhook(request)

@app.get("/dns-test")
async def dns():
    return await dns_test()

@app.get("/ai-test")
async def ai():
    return await test_ai_response()