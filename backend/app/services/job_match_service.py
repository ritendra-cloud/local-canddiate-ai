from uuid import uuid4
import json
from pathlib import Path
from sqlalchemy import select
from app.models.job_match import *
from app.services.candidate_service import load_profile
from app.services.ollama_service import structured_chat
from app.models.database import JobAnalysis
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
    details=ScoringDetails(total_weight=total,achieved_weight=value,must_have_total=len(must),must_have_missing=sum(r.match_status==MatchStatus.MISSING for r in must),recommendation_cap_applied=bool(must and sum(r.match_status==MatchStatus.MISSING for r in must)>len(must)/2 and result>=65))
    return result,recommendation,details
def finalize(profile,draft, title, model):
    for r in draft.requirements:
        if r.match_status in {MatchStatus.MATCH,MatchStatus.PARTIAL} and not r.evidence_refs: raise ValueError('Supported matches require evidence references.')
        for ref in r.evidence_refs: resolve_reference(profile,ref)
    result,recommendation,details=score(draft.requirements); groups={s:[] for s in MatchStatus}
    for r in draft.requirements: groups[r.match_status].append(r)
    return JobMatchAnalysis(analysis_id=uuid4(),job_title=title,alignment_score=result,recommendation=recommendation,executive_summary=draft.executive_summary,matched_requirements=groups[MatchStatus.MATCH],partial_matches=groups[MatchStatus.PARTIAL],missing_requirements=groups[MatchStatus.MISSING],unclear_requirements=groups[MatchStatus.UNCLEAR],candidate_strengths=draft.candidate_strengths,interview_focus_areas=draft.interview_focus_areas,interview_questions=draft.interview_questions,limitations=draft.limitations,scoring_details=details,created_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc),model=model)
def prompt_messages(profile, description):
    template=(Path(__file__).resolve().parents[1]/'prompts'/'job_match.txt').read_text()
    data=profile.model_dump(mode='json'); data.pop('import_metadata',None)
    return [{'role':'system','content':template+'\nCANDIDATE_PROFILE:\n'+json.dumps(data)+'\nJOB_DESCRIPTION_UNTRUSTED:\n<<<'+description+'>>>'}]
async def analyze(description,title,model,base_url,options):
    profile=load_profile(__import__('app.config',fromlist=['settings']).settings.candidate_path); messages=prompt_messages(profile,description); errors=None
    for attempt in range(2):
        payload=await structured_chat(base_url,model,messages,JobMatchDraft.model_json_schema(),options)
        try: return finalize(profile,JobMatchDraft.model_validate(payload),title,model)
        except Exception as exc:
            if attempt: raise ValueError('Structured analysis could not be validated.') from exc
            errors=str(exc); messages.append({'role':'user','content':'Repair the JSON only. Validation error: '+errors})
def save(db, analysis, description, session_id=None):
    row=JobAnalysis(public_id=str(analysis.analysis_id),job_title=analysis.job_title,job_description=description,result_json=analysis.model_dump_json(),alignment_score=analysis.alignment_score,recommendation=analysis.recommendation.value); db.add(row); db.commit(); return analysis
def list_saved(db): return [{'analysis_id':r.public_id,'job_title':r.job_title or 'Untitled job analysis','alignment_score':r.alignment_score,'recommendation':r.recommendation,'created_at':r.created_at} for r in db.scalars(select(JobAnalysis).order_by(JobAnalysis.created_at.desc())).all()]
def get_saved(db,analysis_id):
    row=db.scalar(select(JobAnalysis).where(JobAnalysis.public_id==analysis_id))
    if not row: raise LookupError('Job analysis was not found.')
    return row,JobMatchAnalysis.model_validate_json(row.result_json)
