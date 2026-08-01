from fastapi import APIRouter,HTTPException
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.database import init_database,JobAnalysis
from app.models.job_match import JobMatchRequest
from app.services.job_match_service import analyze,save,list_saved,get_saved
from app.services.session_service import get_session,UnknownSessionError
from app.services.ollama_service import OllamaError
router=APIRouter()
def db(): return sessionmaker(bind=init_database(settings.database_file))()
def err(code,message,retryable=False,status=422): raise HTTPException(status,{'error':{'code':code,'message':message,'retryable':retryable}})
@router.post('/job-match')
async def job_match(request:JobMatchRequest):
    if len(request.job_description)>settings.max_job_description_length: err('JOB_DESCRIPTION_TOO_LONG','Job description exceeds the maximum length.')
    session=db()
    try:
        if request.session_id: get_session(session,str(request.session_id))
        result=await analyze(request.job_description,request.job_title,settings.ollama_model,settings.ollama_base_url,{'temperature':0.0,'num_ctx':settings.chat_num_ctx,'num_predict':3000,'top_p':settings.chat_top_p,'repeat_penalty':settings.chat_repeat_penalty})
        return save(session,result,request.job_description,str(request.session_id) if request.session_id else None)
    except UnknownSessionError: err('SESSION_NOT_FOUND','Conversation session was not found.',False,404)
    except OllamaError: err('OLLAMA_UNAVAILABLE','Local Ollama is unavailable.',True,503)
    except ValueError as exc:
        code='NO_MEANINGFUL_REQUIREMENTS' if 'No meaningful' in str(exc) else 'STRUCTURED_OUTPUT_INVALID'
        err(code,'The local model could not produce a valid job analysis.',True,502)
    except Exception: err('JOB_ANALYSIS_PERSISTENCE_FAILED','The job analysis could not be saved.',True,503)
    finally: session.close()
@router.get('/job-analyses')
def analyses():
    session=db()
    try:return list_saved(session)
    finally:session.close()
@router.get('/job-analyses/{analysis_id}')
def analysis(analysis_id:str):
    session=db()
    try:return get_saved(session,analysis_id)[1]
    except LookupError:err('JOB_ANALYSIS_NOT_FOUND','Job analysis was not found.',False,404)
    finally:session.close()
@router.delete('/job-analyses/{analysis_id}')
def delete_analysis(analysis_id:str):
    session=db()
    try: row,_=get_saved(session,analysis_id);session.delete(row);session.commit();return {'deleted':True}
    except LookupError:err('JOB_ANALYSIS_NOT_FOUND','Job analysis was not found.',False,404)
    finally:session.close()
@router.delete('/job-analyses')
def clear_analyses():
    session=db(); session.query(JobAnalysis).delete();session.commit();session.close();return {'deleted':True}
