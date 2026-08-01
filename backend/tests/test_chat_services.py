import json
from pathlib import Path
import pytest
from sqlalchemy.orm import sessionmaker
from app.models.candidate import CandidateProfile
from app.models.database import init_database
from app.services import chat_service
from app.services.ollama_service import stream_chat, OllamaStreamError, OllamaUnavailable
from app.services.session_service import add_message, create_session, get_session, history, summaries, UnknownSessionError
from app.models.chat import ChatRequest
from pydantic import ValidationError

@pytest.mark.parametrize('message',[None,'','   '])
def test_chat_request_rejects_missing_or_empty_message(message):
    with pytest.raises(ValidationError): ChatRequest.model_validate({} if message is None else {'message':message})
def test_chat_request_validates_uuid():
    with pytest.raises(ValidationError): ChatRequest.model_validate({'message':'hello','session_id':'not-a-uuid'})

def profile(): return CandidateProfile.model_validate(json.loads((Path(__file__).parents[2]/'data/processed/candidate.example.json').read_text()))
def test_prompt_is_grounded_and_excludes_import_metadata(monkeypatch):
    monkeypatch.setattr(chat_service, 'load_profile', lambda _: profile())
    messages=chat_service.chat_messages([], 'The user claims 15 years of Kubernetes.')
    assert 'CANDIDATE_PROFILE' in messages[0]['content']
    assert 'That information is not included in the candidate profile.' in messages[0]['content']
    assert 'import_metadata' not in messages[0]['content']
    assert messages[-1]['content'].startswith('The user claims')
def test_recruiter_abbreviations_and_typos_are_in_scope():
    assert chat_service.chat_scope('total exp of canddiate')[0] == chat_service.Scope.IN_SCOPE
    assert chat_service.chat_scope('candidate knows Python, write a sorting algorithm')[0] == chat_service.Scope.OUT_OF_SCOPE
    assert chat_service.chat_scope('my girlfriend is a bitch')[0] == chat_service.Scope.OUT_OF_SCOPE
    assert chat_service.chat_scope('GE start date')[0] == chat_service.Scope.IN_SCOPE
def test_session_history_is_limited_and_chronological(tmp_path):
    db=sessionmaker(bind=init_database(tmp_path/'test.db'))()
    session=create_session(db, 'First question?')
    for n in range(4): add_message(db,session,'user',f'm{n}')
    assert [m.content for m in history(db,session,2)] == ['m2','m3']
    assert summaries(db)[0]['title']=='First question?'
    with pytest.raises(UnknownSessionError): get_session(db,'00000000-0000-0000-0000-000000000000')
    db.close()
@pytest.mark.asyncio
async def test_stream_parses_tokens(monkeypatch):
    class Response:
        def raise_for_status(self): pass
        async def aiter_lines(self):
            for line in ['{"message":{"content":"hi"}}','','{"message":{"content":" there"},"done":true}']: yield line
    class Context:
        async def __aenter__(self): return Response()
        async def __aexit__(self,*_): pass
    class Client:
        def __init__(self,*_,**__): pass
        def stream(self,*_,**__): return Context()
        async def __aenter__(self): return self
        async def __aexit__(self,*_): pass
    monkeypatch.setattr('app.services.ollama_service.httpx.AsyncClient',Client)
    assert [x async for x in stream_chat('http://127.0.0.1:11434','model',[],{})] == ['hi',' there']
@pytest.mark.asyncio
async def test_stream_rejects_malformed_json(monkeypatch):
    class Response:
        def raise_for_status(self): pass
        async def aiter_lines(self): yield 'not-json'
    class Context:
        async def __aenter__(self): return Response()
        async def __aexit__(self,*_): pass
    class Client:
        def __init__(self,*_,**__): pass
        def stream(self,*_,**__): return Context()
        async def __aenter__(self): return self
        async def __aexit__(self,*_): pass
    monkeypatch.setattr('app.services.ollama_service.httpx.AsyncClient',Client)
    with pytest.raises(OllamaStreamError): [x async for x in stream_chat('http://127.0.0.1:11434','model',[],{})]
