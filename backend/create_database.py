from database import engine, Base
from models import (
    Student,
    TestSession,
    Conversation,
    Evaluation
)

Base.metadata.create_all(bind=engine)
print("SQLite ielts.db database created successfully.")
