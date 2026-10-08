import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.session import engine
from app.db.base import Base
from app.jobs.scheduler import start_scheduler, shutdown_scheduler

# Import Routers
from app.api.auth import router as auth_router
from app.api.controls import router as controls_router
from app.api.scopes import router as scopes_router
from app.api.assignments import router as assignments_router
from app.api.reviews import router as reviews_router
from app.api.requests import router as requests_router
from app.api.evidence import router as evidence_router
from app.api.ai import router as ai_router
from app.api.communications import router as communications_router
from app.api.dashboard import router as dashboard_router
from app.api.audit import router as audit_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is created
    Base.metadata.create_all(bind=engine)
    # Start APScheduler background jobs
    start_scheduler()
    yield
    # Graceful shutdown
    shutdown_scheduler()

app = FastAPI(
    title="AI-Powered Evidence Collection Bot",
    description="End-to-End LOD2 Control Testing & Automated Evidence Collection Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
origins = settings.get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )

# Health Check
@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "ok",
        "service": "AI-Powered Evidence Collection Bot",
        "version": "1.0.0"
    }

# Include all API Routers
app.include_router(auth_router)
app.include_router(controls_router)
app.include_router(scopes_router)
app.include_router(assignments_router)
app.include_router(reviews_router)
app.include_router(requests_router)
app.include_router(evidence_router)
app.include_router(ai_router)
app.include_router(communications_router)
app.include_router(dashboard_router)
app.include_router(audit_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
