import json
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
def test_profile_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'candidate_profile_path', str(tmp_path/'missing.json')); assert TestClient(app).get('/api/profile').status_code==404
def test_profile_success(monkeypatch, tmp_path):
    output=tmp_path/'candidate.json'; output.write_text((__import__('pathlib').Path(__file__).parents[2]/'data/processed/candidate.example.json').read_text()); monkeypatch.setattr(settings, 'candidate_profile_path', str(output))
    response=TestClient(app).get('/api/profile'); assert response.status_code==200 and 'import_metadata' not in response.json()
def test_public_config_hides_paths():
    data=TestClient(app).get('/api/config/public').json(); assert 'path' not in str(data).lower()
