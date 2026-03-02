from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routes.jobs import router as jobs_router

app = FastAPI(title="JobFlow API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(jobs_router)