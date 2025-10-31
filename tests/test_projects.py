import pytest
from api.src.models import Project, Control, Evidence, Report


def test_create_project(client):
    """Test creating a new project"""
    project_data = {
        "name": "Test Project",
        "description": "A test project",
        "status": "active"
    }
    response = client.post("/projects/", json=project_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == project_data["name"]
    assert data["description"] == project_data["description"]
    assert data["status"] == project_data["status"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_get_projects(client):
    """Test getting all projects"""
    # Create a project first
    project_data = {
        "name": "Test Project",
        "description": "A test project",
        "status": "active"
    }
    client.post("/projects/", json=project_data)
    
    response = client.get("/projects/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == project_data["name"]


def test_get_project_by_id(client):
    """Test getting a specific project"""
    # Create a project first
    project_data = {
        "name": "Test Project",
        "description": "A test project",
        "status": "active"
    }
    create_response = client.post("/projects/", json=project_data)
    project_id = create_response.json()["id"]
    
    response = client.get(f"/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == project_data["name"]
    assert data["id"] == project_id


def test_update_project(client):
    """Test updating a project"""
    # Create a project first
    project_data = {
        "name": "Test Project",
        "description": "A test project",
        "status": "active"
    }
    create_response = client.post("/projects/", json=project_data)
    project_id = create_response.json()["id"]
    
    # Update the project
    update_data = {"status": "completed"}
    response = client.put(f"/projects/{project_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["name"] == project_data["name"]  # Unchanged


def test_delete_project(client):
    """Test deleting a project"""
    # Create a project first
    project_data = {
        "name": "Test Project",
        "description": "A test project",
        "status": "active"
    }
    create_response = client.post("/projects/", json=project_data)
    project_id = create_response.json()["id"]
    
    # Delete the project
    response = client.delete(f"/projects/{project_id}")
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(f"/projects/{project_id}")
    assert get_response.status_code == 404


def test_get_nonexistent_project(client):
    """Test getting a project that doesn't exist"""
    response = client.get("/projects/999")
    assert response.status_code == 404


def test_create_project_missing_name(client):
    """Test creating a project without required name field"""
    project_data = {
        "description": "A test project",
        "status": "active"
    }
    response = client.post("/projects/", json=project_data)
    assert response.status_code == 422  # Validation error