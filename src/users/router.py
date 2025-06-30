from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User
from ..schemas import UserCreate, UserResponse, LoginResponse, LoginRequest
from .utils import verify_password, encodeJWT, get_password_hash, get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    
    user_exists =  db.query(User).filter(User.email == user.email).first()
    if user_exists:
        return HTTPException(
            status_code=400, detail="Email already registered"
        )

    db_user = User(name=user.name, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserResponse.model_validate(db_user)

@router.get("/me", response_model=UserResponse)
async def get_user( db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    user_id = user.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        name=db_user.name,
        email=db_user.email
    )

@router.post('/login', response_model=LoginResponse)
def login_user(login_request: LoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == login_request.email).first()
    
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(login_request.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = encodeJWT(str(db_user.id))
    
    return LoginResponse(access_token=access_token, msg="Login successful")





