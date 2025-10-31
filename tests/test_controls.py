import pytest


def test_create_control(client):
    """Test creating a new control"""
    # Create a project first
    project_data = {
        "name": "Test Project",
        "description": "A test project",
        "status": "active"
    }
    project_response = client.post("/projects/", json=project_data)
    project_id = project_response.json()["id"]
    
    # Create a control
    control_data = {
        "project_id": project_id,
        "name": "Test Control",
        "description": "A test control",
        "control_type": "security",
        "status": "active"
    }
    response = client.post("/controls/", json=control_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == control_data["name"]
    assert data["project_id"] == project_id
    assert data["control_type"] == control_data["control_type"]


def test_get_controls(client):
    """Test getting all controls"""
    # Create a project and control first
    project_data = {"name": "Test Project", "status": "active"}
    project_response = client.post("/projects/", json=project_data)
    project_id = project_response.json()["id"]
    
    control_data = {
        "project_id": project_id,
        "name": "Test Control",
        "control_type": "security",
        "status": "active"
    }
    client.post("/controls/", json=control_data)
    
    response = client.get("/controls/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == control_data["name"]


def test_get_controls_by_project(client):
    """Test getting controls filtered by project"""
    # Create two projects with controls
    project1_response = client.post("/projects/", json={"name": "Project 1", "status": "active"})
    project2_response = client.post("/projects/", json={"name": "Project 2", "status": "active"})
    
    project1_id = project1_response.json()["id"]
    project2_id = project2_response.json()["id"]
    
    # Create controls for each project
    client.post("/controls/", json={"project_id": project1_id, "name": "Control 1", "status": "active"})
    client.post("/controls/", json={"project_id": project2_id, "name": "Control 2", "status": "active"})
    
    # Get controls for project 1 only
    response = client.get(f"/controls/?project_id={project1_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Control 1"
    assert data[0]["project_id"] == project1_id


def test_update_control(client):
    """Test updating a control"""
    # Create project and control
    project_response = client.post("/projects/", json={"name": "Test Project", "status": "active"})
    project_id = project_response.json()["id"]
    
    control_response = client.post("/controls/", json={
        "project_id": project_id,
        "name": "Test Control",
        "status": "pending"
    })
    control_id = control_response.json()["id"]
    
    # Update the control
    update_data = {"status": "active"}
    response = client.put(f"/controls/{control_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"


def test_create_control_invalid_project(client):
    """Test creating a control with invalid project_id"""
    control_data = {
        "project_id": 999,  # Non-existent project
        "name": "Test Control",
        "status": "active"
    }
    response = client.post("/controls/", json=control_data)
    assert response.status_code == 404