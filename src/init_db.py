from src.db import Base, engine
from src.models import User, ChatLogs

def init():
    print("Creating tables")
    Base.metadata.create_all(bind=engine)
    print("Done")

if __name__ == "__main__":
    init()
