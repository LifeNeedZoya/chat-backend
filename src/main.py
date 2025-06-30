from fastapi import FastAPI
from src.users.router import router as users_router
from src.chat.router import router as chat_logs_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(
    users_router,
    responses={404: {"description": "Not found"}},
)

app.include_router(
    chat_logs_router,
    responses={404: {"description": "Not found"}},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return "Up and Running"


