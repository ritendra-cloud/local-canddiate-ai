from fastapi import APIRouter
from app.config import settings
from app.models.database import init_database
from app.services.candidate_service import load_profile, ProfileNotFound
from app.services.ollama_service import status
router=APIRouter()
@router.get('/health')
async def health():
    try: load_profile(settings.candidate_path); profile={'available':True,'valid':True}
    except ProfileNotFound: profile={'available':False,'valid':False}
    except Exception: profile={'available':True,'valid':False}
    try: init_database(settings.database_file); database={'available':True}
    except Exception: database={'available':False}
    return {'application':'online','storage':'local','ollama':await status(settings.ollama_base_url, settings.ollama_model),'candidate_profile':profile,'database':database}
