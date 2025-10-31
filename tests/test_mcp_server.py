import pytest
import httpx


def test_mcp_server_root():
    """Test MCP server root endpoint"""
    response = httpx.get("http://localhost:8001/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "MCP Server - Sample Evidence Provider"
    assert data["status"] == "running"


def test_mcp_server_health():
    """Test MCP server health endpoint"""
    response = httpx.get("http://localhost:8001/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_get_sample_evidence():
    """Test getting all sample evidence"""
    response = httpx.get("http://localhost:8001/sample-evidence")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5  # Based on sample data
    
    # Check first evidence item
    first_evidence = data[0]
    assert "id" in first_evidence
    assert "title" in first_evidence
    assert "evidence_type" in first_evidence


def test_get_sample_evidence_by_id():
    """Test getting sample evidence by ID"""
    response = httpx.get("http://localhost:8001/sample-evidence/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Security Audit Report"
    assert data["evidence_type"] == "audit_report"


def test_get_sample_evidence_by_invalid_id():
    """Test getting sample evidence with invalid ID"""
    response = httpx.get("http://localhost:8001/sample-evidence/999")
    assert response.status_code == 404


def test_get_sample_evidence_by_type():
    """Test getting sample evidence by type"""
    response = httpx.get("http://localhost:8001/sample-evidence/type/audit_report")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["evidence_type"] == "audit_report"


def test_get_sample_evidence_by_invalid_type():
    """Test getting sample evidence with non-existent type"""
    response = httpx.get("http://localhost:8001/sample-evidence/type/nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0  # Empty list for non-existent type