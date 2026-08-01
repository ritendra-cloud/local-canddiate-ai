from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api.health import router as health_router
from app.api.profile import router as profile_router
from app.api.chat import router as chat_router
from app.api.job_match import router as job_match_router
app=FastAPI(title=settings.app_name); app.include_router(health_router, prefix='/api'); app.include_router(profile_router, prefix='/api'); app.include_router(chat_router, prefix='/api'); app.include_router(job_match_router,prefix='/api')
@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    if request.url.path=='/api/job-match':
        code='JOB_DESCRIPTION_REQUIRED' if any(e['loc'][-1]=='job_description' for e in exc.errors()) else 'JOB_DESCRIPTION_INVALID'
        return JSONResponse({'error':{'code':code,'message':'Provide a valid job description.','retryable':False}},status_code=422)
    return JSONResponse({'detail':'Invalid request.'},status_code=422)
DIST=Path(__file__).resolve().parents[2] / 'frontend' / 'dist'
if DIST.exists(): app.mount('/assets', StaticFiles(directory=DIST/'assets'), name='assets')
@app.get('/{path:path}', include_in_schema=False)
async def spa(path: str, request: Request):
    if path.startswith('api/'): return JSONResponse({'detail':'Not found'}, status_code=404)
    index=DIST/'index.html'
    if index.exists(): return FileResponse(index)
    return JSONResponse({'detail':'Frontend build missing. Run scripts/build.sh.'}, status_code=503)
