from datetime import date
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

class CleanModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
class Skill(CleanModel):
    name: Annotated[str, Field(min_length=1)]; level: str | None = None; years: float | None = Field(default=None, ge=0); evidence: str | None = None
class Candidate(CleanModel):
    name: str | None = None; headline: str | None = None; location: str | None = None; professional_summary: str | None = None
    @field_validator('name')
    @classmethod
    def name_not_blank(cls, v):
        if v == '': raise ValueError('name cannot be empty')
        return v
class Education(CleanModel): institution: str | None=None; degree: str | None=None; field: str | None=None; start_date: str | None=None; end_date: str | None=None
class Experience(CleanModel):
    company: str | None=None; role: str | None=None; start_date: str | None=None; end_date: str | None=None; location: str | None=None; responsibilities: list[str]=[]; achievements: list[str]=[]; technologies: list[str]=[]
class Project(CleanModel):
    name: str | None=None; summary: str | None=None; problem: str | None=None; solution: str | None=None; technologies: list[str]=[]; challenges: list[str]=[]; outcomes: list[str]=[]; repository: HttpUrl | None=None
class Certification(CleanModel): name: str | None=None; issuer: str | None=None; date: str | None=None
class ImportMetadata(CleanModel): source_type: str='docx'; imported_at: str; sections_detected: list[str]=[]; warnings: list[str]=[]; unclassified_block_count: int=0
class CandidateProfile(CleanModel):
    schema_version: str='1.0'; last_updated: str; candidate: Candidate; education: list[Education]=[]; skills: dict[str, list[Skill]]={}; experience: list[Experience]=[]; projects: list[Project]=[]; certifications: list[Certification]=[]; achievements: list[str]=[]; publications_and_patents: list[str]=[]; social_links: dict[str, HttpUrl]={}; import_metadata: ImportMetadata
