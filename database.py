import os
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_async_client, AsyncClient
import logging
from config import SUPABASE_URL, SUPABASE_KEY

class DatabaseManager:
    def __init__(self, supabase_url: str = SUPABASE_URL, supabase_key: str = SUPABASE_KEY):
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.supabase: Optional[AsyncClient] = None
        self.logger = logging.getLogger(__name__)

    async def _ensure_connection(self):
        if self.supabase is None:
            await self.connect()

    async def connect(self):
        """Initialize the async client"""
        if not self.supabase:
            self.supabase = await create_async_client(self.supabase_url, self.supabase_key)

    async def create_or_update_user(self, telegram_id: int, username: str = None, 
                                    first_name: str = None, last_name: str = None):
        await self._ensure_connection()
        try:
            existing_user = await self.supabase.table("users").select("id").eq("telegram_id", telegram_id).execute()
            
            user_data = {
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if existing_user.data:
                result = await self.supabase.table("users").update(user_data).eq("telegram_id", telegram_id).execute()
            else:
                user_data["created_at"] = datetime.utcnow().isoformat()
                result = await self.supabase.table("users").insert(user_data).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Error creating/updating user: {e}")
            return None

    async def save_message(self, telegram_id: int, message_text: str, message_type: str):
        await self._ensure_connection()
        try:
            await self.create_or_update_user(telegram_id)
            
            message_data = {
                "telegram_id": telegram_id,
                "message_text": message_text,
                "message_type": message_type,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = await self.supabase.table("messages").insert(message_data).execute()
            await self._ensure_active_session(telegram_id)
            
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Error saving message: {e}")
            return None

    async def get_conversation_history(self, telegram_id: int, limit: int = 10) -> List[Dict]:
        await self._ensure_connection()
        try:
            result = await (self.supabase.table("messages")
                           .select("message_text, message_type, created_at")
                           .eq("telegram_id", telegram_id)
                           .order("created_at", desc=True)
                           .limit(limit)
                           .execute())
            return result.data if result.data else []
        except Exception as e:
            self.logger.error(f"Error getting history: {e}")
            return []

    async def _ensure_active_session(self, telegram_id: int):
        await self._ensure_connection()
        try:
            active = await (self.supabase.table("conversation_sessions")
                            .select("id")
                            .eq("telegram_id", telegram_id)
                            .is_("session_end", "null")
                            .execute())
            
            if not active.data:
                session_data = {
                    "telegram_id": telegram_id,
                    "session_start": datetime.utcnow().isoformat(),
                    "created_at": datetime.utcnow().isoformat()
                }
                await self.supabase.table("conversation_sessions").insert(session_data).execute()
        except Exception as e:
            self.logger.error(f"Error ensuring session: {e}")

db_manager = DatabaseManager()