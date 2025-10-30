from fastapi import FastAPI, HTTPException
from typing import List
from mcp_server.src.sample_data import SampleEvidence, SAMPLE_EVIDENCE

app = FastAPI(
    title="MCP Server - Sample Evidence Provider",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "MCP Server - Sample Evidence Provider",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/sample-evidence", response_model=List[SampleEvidence])
def get_sample_evidence():
    """Get all sample evidence items"""
    return SAMPLE_EVIDENCE


@app.get("/sample-evidence/{evidence_id}", response_model=SampleEvidence)
def get_sample_evidence_by_id(evidence_id: int):
    """Get a specific sample evidence item by ID"""
    for evidence in SAMPLE_EVIDENCE:
        if evidence["id"] == evidence_id:
            return evidence
    raise HTTPException(status_code=404, detail="Evidence not found")


@app.get("/sample-evidence/type/{evidence_type}", response_model=List[SampleEvidence])
def get_sample_evidence_by_type(evidence_type: str):
    """Get sample evidence items by type"""
    filtered = [e for e in SAMPLE_EVIDENCE if e["evidence_type"] == evidence_type]
    return filtered
