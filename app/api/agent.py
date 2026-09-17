# app/api/agent.py
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_optional_user
from app.models.user import User, ChatSession, ChatMessage
from app.schemas.api import ChatRequest, ChatResponse
from app.agent.core import run_agent_turn

router = APIRouter(prefix="/api/agent", tags=["Agent"])

@router.get("/sessions")
def list_chat_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.updated_at.desc()).all()
    return [{"id": s.id, "title": s.title, "created_at": s.created_at, "updated_at": s.updated_at} for s in sessions]


@router.post("/sessions")
def create_chat_session(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = ChatSession(id=str(uuid.uuid4()), user_id=current_user.id, title="New Chat")
    db.add(session)
    db.commit()
    return {"id": session.id, "title": session.title}


@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return [{"role": m.role, "content": m.content} for m in session.messages]


@router.delete("/sessions/{session_id}")
def delete_chat_session(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    db.delete(session)
    db.commit()
    return {"message": "Session deleted."}


@router.post("/chat", response_model=ChatResponse)
def chat_with_agent(req: ChatRequest, current_user: Optional[User] = Depends(get_optional_user), db: Session = Depends(get_db)):
    history = list(req.history) if req.history else []
    session_id = req.session_id

    if current_user:
        if not session_id:
            session_id = str(uuid.uuid4())
            db.add(ChatSession(id=session_id, user_id=current_user.id, title=req.message[:35] + "..."))
            db.commit()
        else:
            s = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
            if s and s.title == "New Chat":
                s.title = req.message[:35] + "..." if len(req.message) > 35 else req.message
                db.commit()

        db.add(ChatMessage(session_id=session_id, user_id=current_user.id, role="user", content=req.message))
        db.commit()

    reply = run_agent_turn(db, history, req.message, user_id=current_user.id if current_user else None)

    if current_user and session_id:
        db.add(ChatMessage(session_id=session_id, user_id=current_user.id, role="assistant", content=reply))
        db.commit()

    return {"reply": reply, "history": history}