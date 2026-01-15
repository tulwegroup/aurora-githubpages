"""
ABSOLUTE MINIMAL - Just FastAPI, nothing else
"""
import os
os.environ['PYTHONUNBUFFERED'] = '1'

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime

app = FastAPI(title="Aurora OSI v3")

@app.get("/system/health")
async def health():
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.1.0"
    })

@app.get("/")
async def root():
    return JSONResponse({"message": "Aurora OSI v3", "status": "running"})

# Try backend if it exists
try:
    from backend.main import app as backend_app
    app = backend_app
except:
    pass

