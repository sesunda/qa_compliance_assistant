import pytest


def test_create_evidence(client):
    """Test creating evidence"""
    # Create project and control
    project_response = client.post("/projects/", json={"name": "Test Project", "status": "active"})
    project_id = project_response.json()["id"]
    
    control_response = client.post("/controls/", json={
        "project_id": project_id,
        "name": "Test Control",
        "status": "active"
    })
    control_id = control_response.json()["id"]
    
    # Create evidence
    evidence_data = {
        "control_id": control_id,
        "title": "Test Evidence",
        "description": "Test evidence description",
        "evidence_type": "document",
        "verified": True
    }
    response = client.post("/evidence/", json=evidence_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == evidence_data["title"]
    assert data["control_id"] == control_id
    assert data["verified"] == True


def test_get_evidence(client):
    """Test getting all evidence"""
    # Create project, control, and evidence
    project_response = client.post("/projects/", json={"name": "Test Project", "status": "active"})
    project_id = project_response.json()["id"]
    
    control_response = client.post("/controls/", json={
        "project_id": project_id,
        "name": "Test Control",
        "status": "active"
    })
    control_id = control_response.json()["id"]
    
    evidence_data = {
        "control_id": control_id,
        "title": "Test Evidence",
        "evidence_type": "document"
    }
    client.post("/evidence/", json=evidence_data)
    
    response = client.get("/evidence/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == evidence_data["title"]


def test_get_evidence_by_control(client):
    """Test getting evidence filtered by control"""
    # Create project and two controls
    project_response = client.post("/projects/", json={"name": "Test Project", "status": "active"})
    project_id = project_response.json()["id"]
    
    control1_response = client.post("/controls/", json={
        "project_id": project_id,
        "name": "Control 1",
        "status": "active"
    })
    control2_response = client.post("/controls/", json={
        "project_id": project_id,
        "name": "Control 2",
        "status": "active"
    })
    
    control1_id = control1_response.json()["id"]
    control2_id = control2_response.json()["id"]
    
    # Create evidence for each control
    client.post("/evidence/", json={"control_id": control1_id, "title": "Evidence 1"})
    client.post("/evidence/", json={"control_id": control2_id, "title": "Evidence 2"})
    
    # Get evidence for control 1 only
    response = client.get(f"/evidence/?control_id={control1_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Evidence 1"
    assert data[0]["control_id"] == control1_id


def test_update_evidence(client):
    """Test updating evidence"""
    # Create project, control, and evidence
    project_response = client.post("/projects/", json={"name": "Test Project", "status": "active"})
    project_id = project_response.json()["id"]
    
    control_response = client.post("/controls/", json={
        "project_id": project_id,
        "name": "Test Control",
        "status": "active"
    })
    control_id = control_response.json()["id"]
    
    evidence_response = client.post("/evidence/", json={
        "control_id": control_id,
        "title": "Test Evidence",
        "verified": False
    })
    evidence_id = evidence_response.json()["id"]
    
    # Update evidence
    update_data = {"verified": True}
    response = client.put(f"/evidence/{evidence_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["verified"] == True


def test_create_evidence_invalid_control(client):
    """Test creating evidence with invalid control_id"""
    evidence_data = {
        "control_id": 999,  # Non-existent control
        "title": "Test Evidence"
    }
    response = client.post("/evidence/", json=evidence_data)
    assert response.status_code == 404