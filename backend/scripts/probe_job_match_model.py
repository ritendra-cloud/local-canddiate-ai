"""Development-only local structured-output probe; it never sends candidate data."""
import asyncio, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import settings
from app.models.job_match import RequirementExtraction
from app.services.ollama_service import structured_chat_details

async def probe(model: str):
    message='Return one Selenium automation requirement only. Use the supplied JSON schema.'
    try:
        payload, diagnostics=await structured_chat_details(settings.ollama_base_url,model,[{'role':'user','content':message}],RequirementExtraction.model_json_schema(),{'temperature':0,'num_ctx':settings.job_match_num_ctx,'num_predict':256})
        RequirementExtraction.model_validate(payload)
        print({'model':model,'valid':True,**diagnostics})
    except Exception as exc:
        print({'model':model,'valid':False,'error_category':type(exc).__name__})
async def main():
    for model in (settings.chat_model,settings.ollama_job_match_model): await probe(model)
if __name__=='__main__': asyncio.run(main())
