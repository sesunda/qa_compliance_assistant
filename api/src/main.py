# QA Compliance Assistant - Main FastAPI Application
# Last updated: 2025-11-10 - User management permissions fix deployment
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

from api.src.config import settings
from api.src.routers import projects, controls, evidence, reports
from api.src.routers import control_catalog
from api.src.workers.task_worker import get_worker
from api.src.workers.task_handlers import TASK_HANDLERS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Starts the background task worker on startup and stops it on shutdown.
    """
    # Startup
    logger.info("Starting async database...")
    from api.src.db.async_database import async_db
    await async_db.connect()
    
    logger.info("Starting background task worker...")
    worker = get_worker()
    
    # Register all task handlers
    for task_type, handler in TASK_HANDLERS.items():
        worker.register_handler(task_type, handler)
    
    # Start worker in background
    worker_task = asyncio.create_task(worker.start())
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down background task worker...")
    await worker.stop()
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    
    logger.info("Closing async database...")
    await async_db.disconnect()
    
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# CRITICAL: Middleware order matters! They execute in REVERSE order of addition.
# Add CORS first so it processes last (adds headers to final response)

# CORS middleware - MUST be added first
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Add OPTIONS for preflight
    allow_headers=["Content-Type", "Authorization"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Only add HSTS in production with HTTPS
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Proxy headers middleware - handles X-Forwarded-Proto from Azure
class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to handle X-Forwarded-* headers from Azure proxy"""
    async def dispatch(self, request: Request, call_next):
        # Check for X-Forwarded-Proto header (set by Azure Application Gateway/Front Door)
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto == "https":
            # Override the request URL scheme to https
            request.scope["scheme"] = "https"
        
        response = await call_next(request)
        return response

app.add_middleware(ProxyHeadersMiddleware)

# Exception handler to ensure CORS headers on errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that ensures CORS headers are always added,
    even when exceptions occur before response middleware runs.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Create error response
    response = JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.API_VERSION == "dev" else "An error occurred"
        }
    )
    
    # Manually add CORS headers
    origin = request.headers.get("origin")
    if origin in settings.ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
    
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP exception handler that ensures CORS headers on HTTP errors.
    """
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    
    # Manually add CORS headers
    origin = request.headers.get("origin")
    if origin in settings.ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
    
    return response

# Include routers
app.include_router(projects.router)
app.include_router(controls.router)
app.include_router(evidence.router)
app.include_router(reports.router)
app.include_router(control_catalog.router)

# Import and include routers
from api.src.routers import auth, rag, agent_tasks, agencies, conversations, assessments, findings, analytics, agentic_chat, templates, task_stream
app.include_router(auth.router)
app.include_router(rag.router)
app.include_router(agent_tasks.router)
app.include_router(agencies.router)
app.include_router(conversations.router)
app.include_router(assessments.router)
app.include_router(findings.router)
app.include_router(analytics.router)
app.include_router(agentic_chat.router)
app.include_router(templates.router)
app.include_router(task_stream.router)


@app.get("/")
def root():
    return {
        "message": "Quantique Compliance Assistant API",
        "version": settings.API_VERSION,
        "status": "running"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/admin/migrate")
async def run_migrations():
    """Run database migrations - admin only endpoint"""
    import subprocess
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        return {
            "status": "success",
            "output": result.stdout,
            "message": "Migrations completed successfully"
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "output": e.stdout,
            "error": e.stderr,
            "message": "Migration failed"
        }


@app.post("/admin/reset-database")
async def reset_database():
    """Reset entire database and apply consolidated migration"""
    from api.src.database import SessionLocal
    from sqlalchemy import text
    
    db = SessionLocal()
    try:
        # Drop all tables
        db.execute(text("DROP SCHEMA public CASCADE"))
        db.execute(text("CREATE SCHEMA public"))
        db.execute(text("GRANT ALL ON SCHEMA public TO qca_admin"))
        db.execute(text("GRANT ALL ON SCHEMA public TO public"))
        db.commit()
        
        return {
            "status": "success",
            "message": "Database reset complete. Restart container to apply migration 001 and seed admin user."
        }
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to reset database"
        }
    finally:
        db.close()


@app.post("/admin/seed-users")
async def seed_users():
    """Seed default admin user"""
    try:
        from api.scripts.seed_auth import seed_auth_system
        seed_auth_system()
        return {
            "status": "success",
            "message": "Admin user seeded successfully. Login: admin / admin123"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to seed admin user"
        }
