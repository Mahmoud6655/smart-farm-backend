from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user_message = Column(Text)  # رسالة المزارع
    bot_response = Column(Text)  # رد الذكاء الاصطناعي
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())