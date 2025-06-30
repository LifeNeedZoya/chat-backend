import time
import os
import jwt
from passlib.context import CryptContext
from fastapi import Request, HTTPException


JWT_SECRET = os.getenv("SECRET_KEY")
JWT_ALGORITHM = os.getenv("ALGORITHM")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def encodeJWT(user_id: str):
    payload = {
        "user_id": user_id,
        "expires": time.time() + 3600 # 60 minutes
    }
    
    if not JWT_SECRET or not JWT_ALGORITHM:
        raise ValueError("JWT_SECRET and JWT_ALGORITHM must be set in environment variables")
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token

def decodeJWT(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except:
        return False
    

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password) 

def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):

        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = auth_header.split()[1]
    try:
        payload = decodeJWT(token)
        if not payload:
            
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
