import os
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client, Client
import logging
from config import SUPABASE_URL, SUPABASE_KEY


class DatabaseManager:
    def __init__(self, supabase_url: str = SUPABASE_URL, supabase_key: str = SUPABASE_KEY):
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.logger = logging.getLogger(__name__)
    
    def create_or_update_user(self, telegram_id: int, username: str = None, 
                            first_name: str = None, last_name: str = None):
        """Create or update user information"""
        try:
            # Check if user exists
            existing_user = self.supabase.table("users").select("id").eq("telegram_id", telegram_id).execute()
            
            user_data = {
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if existing_user.data:
                # Update existing user
                result = self.supabase.table("users").update(user_data).eq("telegram_id", telegram_id).execute()
            else:
                # Create new user
                user_data["created_at"] = datetime.utcnow().isoformat()
                result = self.supabase.table("users").insert(user_data).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            self.logger.error(f"Error creating/updating user: {e}")
            return None
    
    def save_message(self, telegram_id: int, message_text: str, message_type: str):
        """Save a message to the database"""
        try:
            # Ensure user exists
            self.create_or_update_user(telegram_id)
            
            # Save message
            message_data = {
                "telegram_id": telegram_id,
                "message_text": message_text,
                "message_type": message_type,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("messages").insert(message_data).execute()
            
            # Ensure active session exists
            self._ensure_active_session(telegram_id)
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            self.logger.error(f"Error saving message: {e}")
            return None
    
    def get_conversation_history(self, telegram_id: int, limit: int = 10) -> List[Dict]:
        """Get conversation history for a user"""
        try:
            result = (self.supabase.table("messages")
                     .select("message_text, message_type, created_at")
                     .eq("telegram_id", telegram_id)
                     .order("created_at", desc=True)
                     .limit(limit)
                     .execute())
            
            return result.data if result.data else []
            
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return []
    
    def get_formatted_history(self, telegram_id: int, limit: int = 10) -> str:
        """Get formatted conversation history for Groq"""
        history = self.get_conversation_history(telegram_id, limit)
        
        if not history:
            return ""
        
        # Reverse to get chronological order
        history.reverse()
        
        formatted_history = "Previous conversation:\n"
        for msg in history:
            role = "User" if msg['message_type'] == 'user' else "Assistant"
            formatted_history += f"{role}: {msg['message_text']}\n"
        
        return formatted_history
    
    def _ensure_active_session(self, telegram_id: int):
        """Ensure an active session exists for the user"""
        try:
            # Check for active session
            active_session = (self.supabase.table("conversation_sessions")
                             .select("id")
                             .eq("telegram_id", telegram_id)
                             .is_("session_end", "null")
                             .execute())
            
            if not active_session.data:
                # Create new session
                session_data = {
                    "telegram_id": telegram_id,
                    "session_start": datetime.utcnow().isoformat(),
                    "created_at": datetime.utcnow().isoformat()
                }
                self.supabase.table("conversation_sessions").insert(session_data).execute()
                
        except Exception as e:
            self.logger.error(f"Error ensuring active session: {e}")
    
    def start_new_session(self, telegram_id: int):
        """Start a new conversation session"""
        try:
            # End previous sessions
            self.supabase.table("conversation_sessions").update({
                "session_end": datetime.utcnow().isoformat()
            }).eq("telegram_id", telegram_id).is_("session_end", "null").execute()
            
            # Start new session
            session_data = {
                "telegram_id": telegram_id,
                "session_start": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
            result = self.supabase.table("conversation_sessions").insert(session_data).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            self.logger.error(f"Error starting new session: {e}")
            return None
    
    def get_user_stats(self, telegram_id: int) -> Dict:
        """Get user conversation statistics"""
        try:
            # Get message counts
            message_stats = (self.supabase.table("messages")
                           .select("message_type")
                           .eq("telegram_id", telegram_id)
                           .execute())
            
            if not message_stats.data:
                return {
                    "total_messages": 0,
                    "user_messages": 0,
                    "assistant_messages": 0,
                    "first_message": None,
                    "last_message": None
                }
            
            total_messages = len(message_stats.data)
            user_messages = len([m for m in message_stats.data if m['message_type'] == 'user'])
            assistant_messages = len([m for m in message_stats.data if m['message_type'] == 'assistant'])
            
            # Get first and last message timestamps
            timestamps = [m['created_at'] for m in message_stats.data]
            first_message = min(timestamps) if timestamps else None
            last_message = max(timestamps) if timestamps else None
            
            return {
                "total_messages": total_messages,
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "first_message": first_message,
                "last_message": last_message
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user stats: {e}")
            return {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "first_message": None,
                "last_message": None
            }

# Global database instance
try:
    db_manager = DatabaseManager()
except ValueError as e:
    print(f"Database initialization failed: {e}")
    print("Please set SUPABASE_URL and SUPABASE_KEY environment variables")
    db_manager = None
except Exception as e:
    print(f"Unexpected database error: {e}")
    db_manager = None
