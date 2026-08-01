import asyncio, json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.chat import ChatRequest
from app.models.database import init_database
from app.services.chat_service import chat_messages, generation_options
from app.services.ollama_service import stream_chat, OllamaError
from app.services.session_service import add_message, create_session, get_session, history, summaries, UnknownSessionError

router=APIRouter()
def db_session(): return sessionmaker(bind=init_database(settings.database_file))()
def event(name, data): return f'event: {name}\ndata: {json.dumps(data)}\n\n'
@router.post('/chat')
async def chat(payload: ChatRequest, request: Request):
    if len(payload.message)>settings.max_user_message_length: raise HTTPException(422,'Message exceeds the maximum length.')
    db=db_session()
    try:
        session=get_session(db,str(payload.session_id)) if payload.session_id else create_session(db,payload.message)
        prior=history(db,session,settings.max_history_messages)
        add_message(db,session,'user',payload.message)
        messages=chat_messages(prior,payload.message)
    except UnknownSessionError as exc: db.close(); raise HTTPException(404,str(exc))
    except FileNotFoundError: db.close(); raise HTTPException(503,'Candidate profile is unavailable.')
    except Exception: db.close(); raise HTTPException(503,'Candidate profile is invalid or local storage is unavailable.')
    async def generate():
        chunks=[]
        try:
            yield event('session',{'session_id':session.public_id})
            async for chunk in stream_chat(settings.ollama_base_url,settings.chat_model,messages,generation_options()):
                if await request.is_disconnected(): return
                chunks.append(chunk); yield event('token',{'content':chunk})
            saved=add_message(db,session,'assistant',''.join(chunks))
            yield event('complete',{'session_id':session.public_id,'message_id':str(saved.id)})
        except asyncio.CancelledError: return
        except OllamaError as exc: yield event('error',{'code':'OLLAMA_UNAVAILABLE','message':'Local Ollama is unavailable or returned an invalid response.'})
        finally: db.close()
    return StreamingResponse(generate(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})
@router.get('/sessions')
def list_sessions():
    db=db_session()
    try: return summaries(db)
    finally: db.close()
@router.get('/sessions/{session_id}')
def read_session(session_id: str):
    db=db_session()
    try:
        s=get_session(db,session_id); return {'session_id':s.public_id,'title':s.title,'created_at':s.created_at,'updated_at':s.updated_at,'messages':[{'id':str(m.id),'role':m.role,'content':m.content,'status':m.status,'created_at':m.created_at} for m in sorted(s.messages,key=lambda m:(m.created_at,m.id))]}
    except UnknownSessionError as exc: raise HTTPException(404,str(exc))
    finally: db.close()
@router.delete('/sessions/{session_id}')
def delete_session(session_id: str):
    db=db_session()
    try: db.delete(get_session(db,session_id)); db.commit(); return {'deleted':True}
    except UnknownSessionError as exc: raise HTTPException(404,str(exc))
    finally: db.close()
@router.delete('/sessions')
def clear_sessions():
    db=db_session()
    try:
        for s in db.query(__import__('app.models.database',fromlist=['Session']).Session).all(): db.delete(s)
        db.commit(); return {'deleted':True}
    finally: db.close()
