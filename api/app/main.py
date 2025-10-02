from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="DocTalk API", version="0.0.1")

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}
