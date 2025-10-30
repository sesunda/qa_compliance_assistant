from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.src.config import settings
from api.src.routers import projects, controls, evidence, reports

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router)
app.include_router(controls.router)
app.include_router(evidence.router)
app.include_router(reports.router)


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
