from uuid import uuid4
from app.models.job_match import *
WEIGHTS={Importance.MUST_HAVE:3,Importance.PREFERRED:1.5,Importance.RESPONSIBILITY:1,Importance.UNCLEAR:.5}; VALUES={MatchStatus.MATCH:1,MatchStatus.PARTIAL:.5,MatchStatus.MISSING:0,MatchStatus.UNCLEAR:0}
def resolve_reference(profile, ref:str):
    if not ref or ref.startswith('import_metadata') or '..' in ref or '/' in ref: raise ValueError('Invalid evidence reference.')
    value=profile.model_dump(mode='json');
    for segment in ref.replace('[','.').replace(']','').split('.'):
        if not segment: continue
        if isinstance(value,list):
            if not segment.isdigit() or int(segment)>=len(value): raise ValueError('Invalid evidence reference.')
            value=value[int(segment)]
        elif isinstance(value,dict) and segment in value and segment!='import_metadata': value=value[segment]
        else: raise ValueError('Invalid evidence reference.')
    return value
def score(requirements):
    if not requirements: raise ValueError('No meaningful job requirements were extracted.')
    total=sum(WEIGHTS[r.importance] for r in requirements); value=sum(WEIGHTS[r.importance]*VALUES[r.match_status] for r in requirements); result=round(value/total*100)
    recommendation=Recommendation.STRONG_INTERVIEW if result>=80 else Recommendation.INTERVIEW if result>=65 else Recommendation.CONSIDER if result>=50 else Recommendation.NOT_RECOMMENDED
    must=[r for r in requirements if r.importance==Importance.MUST_HAVE]
    if must and sum(r.match_status==MatchStatus.MISSING for r in must)>len(must)/2 and recommendation in {Recommendation.STRONG_INTERVIEW,Recommendation.INTERVIEW}: recommendation=Recommendation.CONSIDER
    return result,recommendation
def finalize(profile,draft, title, model):
    for r in draft.requirements:
        if r.match_status in {MatchStatus.MATCH,MatchStatus.PARTIAL} and not r.evidence_refs: raise ValueError('Supported matches require evidence references.')
        for ref in r.evidence_refs: resolve_reference(profile,ref)
    result,recommendation=score(draft.requirements); groups={s:[] for s in MatchStatus}
    for r in draft.requirements: groups[r.match_status].append(r)
    return JobMatchAnalysis(analysis_id=uuid4(),job_title=title,alignment_score=result,recommendation=recommendation,executive_summary=draft.executive_summary,matched_requirements=groups[MatchStatus.MATCH],partial_matches=groups[MatchStatus.PARTIAL],missing_requirements=groups[MatchStatus.MISSING],unclear_requirements=groups[MatchStatus.UNCLEAR],candidate_strengths=draft.candidate_strengths,interview_focus_areas=draft.interview_focus_areas,interview_questions=draft.interview_questions,limitations=draft.limitations,created_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc),model=model)
