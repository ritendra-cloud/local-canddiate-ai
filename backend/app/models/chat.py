from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
class ChatRequest(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True)
    session_id: UUID | None=None
    message: str = Field(min_length=1)
    @field_validator('message')
    @classmethod
    def nonempty(cls, value):
        if not value.strip(): raise ValueError('message must not be empty')
        return value
