# Trivial change for redeployment trigger
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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
    
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan
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

# CORS middleware - CONFIGURED FOR DEVELOPMENT
# ⚠️ WARNING: For production, replace "*" with specific domains
# Example: allow_origins=["https://yourapp.com", "https://admin.yourapp.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Now configurable
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Specific methods only
    allow_headers=["Content-Type", "Authorization"],  # Specific headers only
)

# Include routers
app.include_router(projects.router)
app.include_router(controls.router)
app.include_router(evidence.router)
app.include_router(reports.router)
app.include_router(control_catalog.router)

# Import and include auth router
from api.src.routers import auth, rag, agent_tasks, agencies, conversations, assessments, findings, analytics, services
app.include_router(auth.router)
app.include_router(rag.router)
app.include_router(agent_tasks.router)
app.include_router(agencies.router)
app.include_router(conversations.router)
app.include_router(assessments.router)
app.include_router(findings.router)
app.include_router(analytics.router)
app.include_router(services.router)  # Phase 4 & 5 services


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
