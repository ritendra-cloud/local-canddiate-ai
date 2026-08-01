import json
from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.config import settings
from app.models.job_match import JobMatchDraft,JobRequirementMatch,Category,Importance,MatchStatus,Confidence
from app.services.job_match_service import finalize
from app.models.candidate import CandidateProfile

@pytest.fixture
def client(monkeypatch,tmp_path):
    profile=tmp_path/'candidate.json'; profile.write_text(json.dumps({'schema_version':'1','last_updated':'now','candidate':{'name':'Fictional'},'education':[],'skills':{'tools':[{'name':'Selenium'}]},'experience':[],'projects':[],'certifications':[],'achievements':[],'publications_and_patents':[],'social_links':{},'import_metadata':{'imported_at':'now'}}))
    monkeypatch.setattr(settings,'candidate_profile_path',str(profile));monkeypatch.setattr(settings,'database_path',str(tmp_path/'db.sqlite'))
    async def fake(*_):
        candidate=CandidateProfile.model_validate(json.loads(profile.read_text()))
        draft=JobMatchDraft(executive_summary='Grounded.',requirements=[JobRequirementMatch(requirement='Selenium',category=Category.AUTOMATION,importance=Importance.MUST_HAVE,match_status=MatchStatus.MATCH,evidence_refs=['skills.tools[0].name'],explanation='Profile skill',confidence=Confidence.HIGH)])
        return finalize(candidate,draft,'QA','local')
    monkeypatch.setattr('app.api.job_match.analyze',fake)
    return TestClient(app)
def test_job_match_persists_and_crud(client):
    response=client.post('/api/job-match',json={'job_description':'Need Selenium','job_title':'QA'})
    assert response.status_code==200; result=response.json(); assert result['alignment_score']==100
    assert result['matched_requirements'][0]['resolved_evidence'][0]['value']=='Selenium'
    analysis_id=result['analysis_id']; assert 'id' not in client.get('/api/job-analyses').json()[0]
    assert client.get(f'/api/job-analyses/{analysis_id}').status_code==200
    assert client.delete(f'/api/job-analyses/{analysis_id}').json()=={'deleted':True}
    assert client.get(f'/api/job-analyses/{analysis_id}').status_code==404
def test_job_match_validation_and_failure(client,monkeypatch):
    assert client.post('/api/job-match',json={'job_description':'   '}).status_code==422
    assert client.post('/api/job-match',json={'job_description':'x'*20001}).status_code==422
    async def invalid(*_): raise ValueError('bad output')
    monkeypatch.setattr('app.api.job_match.analyze',invalid)
    response=client.post('/api/job-match',json={'job_description':'Need Rust'})
    assert response.status_code==502 and response.json()['detail']['error']['code']=='STRUCTURED_OUTPUT_INVALID' and 'bad output' not in response.text
