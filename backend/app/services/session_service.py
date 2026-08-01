from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import func, select, delete
from sqlalchemy.orm import Session as DbSession
from app.models.database import Session, Message
class UnknownSessionError(LookupError): pass
def title_from(message: str) -> str: return message.strip().replace('\n',' ')[:72]
def get_session(db: DbSession, public_id: str) -> Session:
    session=db.scalar(select(Session).where(Session.public_id==public_id))
    if not session: raise UnknownSessionError('Conversation session was not found.')
    return session
def create_session(db: DbSession, message: str) -> Session:
    session=Session(public_id=str(uuid4()), title=title_from(message)); db.add(session); db.commit(); db.refresh(session); return session
def add_message(db: DbSession, session: Session, role: str, content: str, status: str='COMPLETE') -> Message:
    message=Message(session_id=session.id,role=role,content=content,status=status); session.updated_at=datetime.now(timezone.utc); db.add(message); db.commit(); db.refresh(message); return message
def history(db: DbSession, session: Session, limit: int):
    messages=db.scalars(select(Message).where(Message.session_id==session.id, Message.status=='COMPLETE').order_by(Message.created_at.desc(), Message.id.desc()).limit(limit)).all()
    return list(reversed(messages))
def summaries(db: DbSession):
    rows=db.execute(select(Session, func.count(Message.id)).outerjoin(Message).group_by(Session.id).order_by(Session.updated_at.desc())).all()
    return [{'session_id':s.public_id,'title':s.title,'created_at':s.created_at,'updated_at':s.updated_at,'message_count':count} for s,count in rows]
