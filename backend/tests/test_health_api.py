from fastapi.testclient import TestClient
from app.main import app
def test_health_response(monkeypatch):
    async def unavailable(*_): return {'reachable':False,'base_url':'http://127.0.0.1:11434','configured_model':'qwen2.5-coder:7b','model_available':False}
    monkeypatch.setattr('app.api.health.status', unavailable); response=TestClient(app).get('/api/health'); assert response.status_code==200 and response.json()['ollama']['reachable'] is False
