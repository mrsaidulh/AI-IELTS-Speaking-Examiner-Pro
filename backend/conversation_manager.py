from database import SessionLocal
from models import Conversation

def save_conversation(session_id, part, question, answer):
    db = SessionLocal()
    try:
        conversation = Conversation(
            session_id=session_id,
            part=part,
            question=question,
            answer=answer
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    finally:
        db.close()

def get_conversations(session_id):
    db = SessionLocal()
    try:
        return db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).order_by(Conversation.created_at).all()
    finally:
        db.close()
