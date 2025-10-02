from fastapi import FastAPI, APIRouter
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

from .routes.detect import router as detect_router
from .routes.simplify import router as simplify_router
from .routes.spellcheck import router as spellcheck_router
from .routes.classify import router as classify_router

app = FastAPI(title="DocTalk API", version="0.0.1")

# allow local web dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health
@app.get("/api/v1/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

# API v1 router
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(detect_router)
api_v1.include_router(simplify_router)
api_v1.include_router(spellcheck_router)
api_v1.include_router(classify_router)
app.include_router(api_v1)
