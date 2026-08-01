import json
from pathlib import Path
import pytest
from app.models.candidate import CandidateProfile
from app.models.job_match import *
from app.services.job_match_service import resolve_reference,resolved_evidence,score,finalize
@pytest.fixture
def profile(): return CandidateProfile.model_validate(json.loads((Path(__file__).parents[2]/'data/processed/candidate.example.json').read_text()))
def requirement(status=MatchStatus.MATCH,importance=Importance.MUST_HAVE,refs=['skills.REPLACE CATEGORY[0].name']): return JobRequirementMatch(requirement='Skill',category=Category.TECHNICAL_SKILL,importance=importance,match_status=status,evidence_refs=refs,explanation='evidence',confidence=Confidence.HIGH)
def test_evidence_resolver_is_safe(profile):
    assert resolve_reference(profile,'skills.REPLACE CATEGORY[0].name')=='REPLACE SKILL'
    for value in ['import_metadata.source_type','skills.__dict__','../candidate.json','skills.x[99]']:
        with pytest.raises(ValueError): resolve_reference(profile,value)
def test_score_and_must_have_cap():
    requirements=[requirement(MatchStatus.MATCH),requirement(MatchStatus.MISSING),requirement(MatchStatus.MISSING)] + [requirement(MatchStatus.MATCH,Importance.PREFERRED) for _ in range(10)]
    result,recommendation,details=score(requirements)
    assert result>=65 and recommendation==Recommendation.CONSIDER and details.recommendation_cap_applied
def test_supported_match_requires_evidence(profile):
    draft=JobMatchDraft(executive_summary='summary',requirements=[requirement(refs=[])])
    with pytest.raises(ValueError): finalize(profile,draft,None,'model')
def test_resolved_evidence_is_human_readable(profile):
    evidence=resolved_evidence(profile,'skills.REPLACE CATEGORY[0].name')
    assert evidence.reference.endswith('.name') and evidence.value=='REPLACE SKILL' and 'evidence' in evidence.label.lower()
def test_final_analysis_is_python_scored(profile):
    result=finalize(profile,JobMatchDraft(executive_summary='summary',requirements=[requirement()]),'Role','local')
    assert result.alignment_score==100 and result.recommendation==Recommendation.STRONG_INTERVIEW
