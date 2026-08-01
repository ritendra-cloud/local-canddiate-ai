from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api.health import router as health_router
from app.api.profile import router as profile_router
from app.api.chat import router as chat_router
app=FastAPI(title=settings.app_name); app.include_router(health_router, prefix='/api'); app.include_router(profile_router, prefix='/api'); app.include_router(chat_router, prefix='/api')
DIST=Path(__file__).resolve().parents[2] / 'frontend' / 'dist'
if DIST.exists(): app.mount('/assets', StaticFiles(directory=DIST/'assets'), name='assets')
@app.get('/{path:path}', include_in_schema=False)
async def spa(path: str, request: Request):
    if path.startswith('api/'): return JSONResponse({'detail':'Not found'}, status_code=404)
    index=DIST/'index.html'
    if index.exists(): return FileResponse(index)
    return JSONResponse({'detail':'Frontend build missing. Run scripts/build.sh.'}, status_code=503)
