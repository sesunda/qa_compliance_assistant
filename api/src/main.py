from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.src.config import settings
from api.src.routers import projects, controls, evidence, reports
from api.src.routers import control_catalog

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION
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
from api.src.routers import auth, rag
app.include_router(auth.router)
app.include_router(rag.router)


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
