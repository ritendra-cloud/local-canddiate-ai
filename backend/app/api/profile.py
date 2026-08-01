from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from app.config import settings
from app.services.candidate_service import load_profile, public_profile, ProfileNotFound
router=APIRouter()
@router.get('/profile')
def profile():
    try: return public_profile(load_profile(settings.candidate_path))
    except ProfileNotFound as exc: raise HTTPException(404, str(exc))
    except (ValidationError, ValueError): raise HTTPException(422, 'Candidate profile is invalid. Re-import or correct candidate.json.')
@router.get('/config/public')
def public_config(): return {'application_name':settings.app_name,'local_only':True,'configured_model':settings.chat_model,'configured_chat_model':settings.chat_model,'configured_job_match_model':settings.ollama_job_match_model,'max_user_message_length':settings.max_user_message_length,'max_job_description_length':settings.max_job_description_length}
