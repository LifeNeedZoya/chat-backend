from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Dict
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserResponse(BaseModel):
    name: str
    email: EmailStr
    
    model_config = {
        "from_attributes": True
    }

class ChatLogsCreate(BaseModel):
    messages: List[Dict[str, str]]
    
class ChatLogsResponse(BaseModel):
    id: int
    messages: List[Dict[str, str]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
        
class LoginResponse(BaseModel):
    access_token: str
    msg:str = "Login successful"

class LoginRequest(BaseModel):
    email: str
    password: str

class ChatSessionResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    model_config = {
        "from_attributes": True 
    }
