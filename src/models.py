from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    chat_logs = relationship("ChatLogs", back_populates="user") 
    chat_sessions = relationship("ChatSessions", back_populates="user")

    
    def __repr__(self):
        return f"<User(name={self.name}, email={self.email})>"
    

class ChatSessions(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, default=f"New Chat at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="chat_sessions")
    
    chat_logs = relationship("ChatLogs", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatSessions(session_id={self.id}, title={self.title}, user_id={self.user_id})>"

class ChatLogs(Base):
    __tablename__ = "chat_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    messages = Column(JSON)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="chat_logs")
    
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
    session = relationship("ChatSessions", back_populates="chat_logs")
    
    def __repr__(self):
        return f"<ChatLogs(session_id={self.session_id}, user_id={self.user_id})>"