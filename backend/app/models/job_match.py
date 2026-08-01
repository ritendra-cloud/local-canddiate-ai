from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
class Category(str,Enum): EXPERIENCE='EXPERIENCE'; TECHNICAL_SKILL='TECHNICAL_SKILL'; TESTING_SKILL='TESTING_SKILL'; AUTOMATION='AUTOMATION'; PROGRAMMING='PROGRAMMING'; API='API'; PERFORMANCE='PERFORMANCE'; DATABASE='DATABASE'; CLOUD_DEVOPS='CLOUD_DEVOPS'; LEADERSHIP='LEADERSHIP'; DOMAIN='DOMAIN'; EDUCATION='EDUCATION'; CERTIFICATION='CERTIFICATION'; RESPONSIBILITY='RESPONSIBILITY'; OTHER='OTHER'
class Importance(str,Enum): MUST_HAVE='MUST_HAVE'; PREFERRED='PREFERRED'; RESPONSIBILITY='RESPONSIBILITY'; UNCLEAR='UNCLEAR'
class MatchStatus(str,Enum): MATCH='MATCH'; PARTIAL='PARTIAL'; MISSING='MISSING'; UNCLEAR='UNCLEAR'
class Confidence(str,Enum): HIGH='HIGH'; MEDIUM='MEDIUM'; LOW='LOW'
class Recommendation(str,Enum): STRONG_INTERVIEW='STRONG_INTERVIEW'; INTERVIEW='INTERVIEW'; CONSIDER='CONSIDER'; NOT_RECOMMENDED='NOT_RECOMMENDED'
class JobMatchRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    job_description:str=Field(min_length=1); job_title:str|None=None; session_id:UUID|None=None; include_interview_questions:bool=True
    @field_validator('job_description')
    @classmethod
    def nonempty(cls,v):
        if not v.strip(): raise ValueError('job_description must not be empty')
        return v
class JobRequirementMatch(BaseModel): requirement:str; category:Category; importance:Importance; match_status:MatchStatus; evidence_refs:list[str]=[]; explanation:str; confidence:Confidence
class JobMatchDraft(BaseModel): executive_summary:str; requirements:list[JobRequirementMatch]; candidate_strengths:list[str]=[]; interview_focus_areas:list[str]=[]; interview_questions:list[str]=[]; limitations:list[str]=[]
class JobMatchAnalysis(BaseModel): analysis_id:UUID; job_title:str|None=None; alignment_score:int=Field(ge=0,le=100); recommendation:Recommendation; executive_summary:str; matched_requirements:list[JobRequirementMatch]=[]; partial_matches:list[JobRequirementMatch]=[]; missing_requirements:list[JobRequirementMatch]=[]; unclear_requirements:list[JobRequirementMatch]=[]; candidate_strengths:list[str]=[]; interview_focus_areas:list[str]=[]; interview_questions:list[str]=[]; limitations:list[str]=[]; created_at:datetime; model:str
