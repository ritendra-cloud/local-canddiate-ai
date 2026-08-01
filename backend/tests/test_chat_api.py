import json
from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.config import settings

@pytest.fixture
def isolated_chat(monkeypatch,tmp_path):
    profile=tmp_path/'candidate.json'; profile.write_text(json.dumps({'schema_version':'1.0','last_updated':'now','candidate':{'name':'Test Candidate'},'education':[],'skills':{},'experience':[],'projects':[],'certifications':[],'achievements':[],'publications_and_patents':[],'social_links':{},'import_metadata':{'imported_at':'now'}}))
    monkeypatch.setattr(settings,'candidate_profile_path',str(profile)); monkeypatch.setattr(settings,'database_path',str(tmp_path/'chat.db'))
    async def mocked(*_):
        yield 'hello'; yield ' world'
    monkeypatch.setattr('app.api.chat.stream_chat',mocked)
    return TestClient(app)
def test_chat_sse_persists_new_session(isolated_chat):
    response=isolated_chat.post('/api/chat',json={'message':'What skills does the candidate have?'})
    assert response.headers['content-type'].startswith('text/event-stream')
    assert response.text.index('event: session') < response.text.index('event: token') < response.text.index('event: complete')
    session_id=json.loads(response.text.split('event: session\ndata: ')[1].split('\n\n')[0])['session_id']
    sessions=isolated_chat.get('/api/sessions').json(); assert sessions[0]['session_id']==session_id and sessions[0]['message_count']==2
    detail=isolated_chat.get(f'/api/sessions/{session_id}').json(); assert [m['content'] for m in detail['messages']]==['What skills does the candidate have?','hello world'] and all('system' != m['role'] for m in detail['messages'])
def test_unknown_session_is_safe(isolated_chat):
    response=isolated_chat.post('/api/chat',json={'session_id':'00000000-0000-0000-0000-000000000000','message':'What skills does the candidate have?'})
    assert response.status_code==404 and 'path' not in response.text.lower() and 'traceback' not in response.text.lower()
def test_stream_failure_saves_only_user(monkeypatch,isolated_chat):
    async def failed(*_):
        if False: yield ''
        raise __import__('app.services.ollama_service',fromlist=['OllamaUnavailable']).OllamaUnavailable('private details')
    monkeypatch.setattr('app.api.chat.stream_chat',failed)
    response=isolated_chat.post('/api/chat',json={'message':'What skills does the candidate have?'})
    assert 'event: error' in response.text and 'private details' not in response.text
    session_id=json.loads(response.text.split('event: session\ndata: ')[1].split('\n\n')[0])['session_id']
    assert len(isolated_chat.get(f'/api/sessions/{session_id}').json()['messages'])==1
def test_session_delete_and_clear(isolated_chat):
    one=isolated_chat.post('/api/chat',json={'message':'one'}).text; two=isolated_chat.post('/api/chat',json={'message':'two'}).text
    sid=lambda text:json.loads(text.split('event: session\ndata: ')[1].split('\n\n')[0])['session_id']
    first,second=sid(one),sid(two); assert isolated_chat.delete(f'/api/sessions/{first}').status_code==200
    assert [s['session_id'] for s in isolated_chat.get('/api/sessions').json()]==[second]
    assert isolated_chat.delete('/api/sessions').status_code==200 and isolated_chat.get('/api/sessions').json()==[]
def test_generic_code_request_is_refused_without_ollama(isolated_chat):
    response=isolated_chat.post('/api/chat',json={'message':'Write Python code to add two numbers.'})
    assert 'general-purpose coding' in response.text and 'event: complete' in response.text
