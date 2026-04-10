from pydantic import BaseModel


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


class AiTestRequest(BaseModel):
    message: str
    telegram_id: int = 12
