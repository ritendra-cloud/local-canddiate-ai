from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[1] / '.env', extra='ignore')
    app_name: str = 'Local CandidateAI'; app_host: str = '127.0.0.1'; app_port: int = 8000
    ollama_base_url: str = 'http://127.0.0.1:11434'; ollama_model: str = 'qwen2.5-coder:7b'
    ollama_chat_model: str | None = 'qwen2.5-coder:7b'; ollama_job_match_model: str = 'qwen2.5-coder:7b'; ollama_job_match_fallback_model: str = ''
    candidate_profile_path: str = '../data/processed/candidate.json'; resume_path: str = '../data/source/resume.docx'; database_path: str = './app/db/candidate_ai.db'
    max_user_message_length: int = 5000; max_job_description_length: int = 20000; max_history_messages: int = 12
    store_conversations: bool = True; log_level: str = 'INFO'
    chat_temperature: float = 0.1; chat_num_ctx: int = 16384; chat_num_predict: int = 1000; chat_top_p: float = 0.9; chat_repeat_penalty: float = 1.1
    job_match_num_ctx: int = 16384; job_match_num_predict: int = 2048; job_match_temperature: float = 0; job_match_requirement_batch_size: int = 2
    job_match_max_evidence_items: int = 8; job_match_max_evidence_value_chars: int = 280; job_match_max_evidence_context_chars: int = 120
    job_match_diagnostics: bool = False
    @field_validator('app_host')
    @classmethod
    def local_host(cls, value: str) -> str:
        if value not in {'127.0.0.1', 'localhost'}: raise ValueError('APP_HOST must be 127.0.0.1 or localhost')
        return value
    def resolve_backend_path(self, value: str) -> Path: return (Path(__file__).resolve().parents[1] / value).resolve()
    @property
    def candidate_path(self) -> Path: return self.resolve_backend_path(self.candidate_profile_path)
    @property
    def resume_file(self) -> Path: return self.resolve_backend_path(self.resume_path)
    @property
    def chat_model(self) -> str: return self.ollama_chat_model or self.ollama_model
    @property
    def database_file(self) -> Path: return self.resolve_backend_path(self.database_path)
settings = Settings()
