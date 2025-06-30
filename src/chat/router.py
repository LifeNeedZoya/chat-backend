from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.responses import  StreamingResponse
import os

from ..db import get_db
from ..models import ChatLogs, ChatSessions
from ..schemas import  ChatLogsResponse, ChatSessionResponse
from .utils import format_messages
from ..users.utils import get_current_user
import google.generativeai as genai
import json
from datetime import datetime

router = APIRouter(prefix="/api/chat", tags=["chat_logs"])
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@router.post("/stream")
async def stream_chat_response(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    try:
        data = await request.json()
        messages = data.get("messages", [])
        session_id = data.get("session", None) 

        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")

        user_id = user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")

        chat_session = None
        existing_messages = []
        
        if session_id:
            chat_session = db.query(ChatSessions).filter(
                ChatSessions.id == session_id,
                ChatSessions.user_id == user_id
            ).first()
            
            if chat_session:
                existing_chat_logs = db.query(ChatLogs).filter(
                    ChatLogs.session_id == session_id, 
                    ChatLogs.user_id == user_id
                ).order_by(ChatLogs.created_at.asc()).all()
                
                for log in existing_chat_logs:
                    if log.messages:
                        existing_messages.extend(log.messages)
            else:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            chat_session = ChatSessions(
                user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(chat_session)
            db.commit()
            db.refresh(chat_session)
            session_id = chat_session.id 
        collected_response = ""
        
        def gemini_stream():
            nonlocal collected_response
            
            try:
                model = genai.GenerativeModel('gemini-2.0-flash')
                
                all_messages = existing_messages + messages
                formatted_messages = format_messages(all_messages)
                
                response = model.generate_content(formatted_messages, stream=True)
                
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        collected_response += chunk.text
                        yield '0:' + json.dumps(chunk.text) + '\n'
                
                completion = {
                    "finishReason": "stop",
                    "usage": {
                        "promptTokens": 0,
                        "completionTokens": 0
                    },
                    "session_id": session_id
                }
                yield 'd:' + json.dumps(completion) + '\n'
                
                try:
                    save_log(collected_response)
                except Exception as db_error:
                    print(f"Database save error: {db_error}")
                    
            except Exception as e:
                error_data = {"error": f"Stream error: {str(e)}"}
                yield 'e:' + json.dumps(error_data) + '\n'

        def save_log(response_text: str):
            try:
                db_chat_log = ChatLogs(
                    session_id=session_id,
                    messages=[
                        {"role": "user", "content": messages[-1]["content"]},
                        {"role": "assistant", "content": response_text}
                    ],
                    user_id=user_id,
                    created_at=datetime.utcnow()
                )
                db.add(db_chat_log)
                db.commit()
                db.refresh(db_chat_log)
                
                chat_session.updated_at = datetime.utcnow()
                db.commit()
                
            except Exception as e:
                print(f"Database error: {e}")
                db.rollback()

        response = StreamingResponse(
            gemini_stream(), 
            media_type='text/plain'
        )
        response.headers['x-vercel-ai-data-stream'] = 'v1'
        response.headers['x-session-id'] = str(session_id)  
        return response

    except Exception as e:
        print("Error during streaming:", e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/session/{session_id}")
def get_session_info(
    session_id: int, 
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    session = db.query(ChatSessions).filter(
        ChatSessions.id == session_id, 
        ChatSessions.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    chat_logs = db.query(ChatLogs).filter(
        ChatLogs.session_id == session_id, 
        ChatLogs.user_id == user_id
    ).order_by(ChatLogs.created_at.asc()).all()
    
    all_messages = []
    for log in chat_logs:
        if log.messages:
            all_messages.extend(log.messages)
    
    return {
        "title": session.title,
        "created_at": session.created_at,
        "messages": all_messages
    }

@router.get("/", response_model=list[ChatSessionResponse])
def get_chat_sessions(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("user_id")
    chat_sessions = db.query(ChatSessions).filter(ChatSessions.user_id == user_id).all()
    
    response = []
    for session in chat_sessions:
        response.append(ChatSessionResponse(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
        
        ))
    return response