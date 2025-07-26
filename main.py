from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager

from app.api.routes import router
from app.core.config import settings
from app.core.logging import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logging.info("Studium backend starting up...")
    yield
    logging.info("Studium backend shutting down...")

tags_metadata = [
    {
        "name": "Document Processing",
        "description": "Upload, process PDF/image files and extract text for educational content generation"
    },
    {
        "name": "AI Content Generation", 
        "description": "Generate Spanish educational content: flashcards, multiple choice, true/false questions, and summaries using Claude Sonnet"
    },
    {
        "name": "System Status",
        "description": "Health checks and AI services status monitoring"
    }
]

app = FastAPI(
    title="Studium API",
    description="AI-powered educational content generation for Spanish-speaking university students",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Studium API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "studium-api"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )