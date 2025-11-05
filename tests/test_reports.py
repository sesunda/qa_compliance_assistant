import pytest


def test_create_report(client):
    """Test creating a report"""
    # Create project first
    project_response = client.post("/projects/", json={"name": "Test Project", "status": "active"})
    project_id = project_response.json()["id"]
    
    # Create report
    report_data = {
        "project_id": project_id,
        "title": "Test Report",
        "content": "This is a test report",
        "report_type": "quarterly"
    }
    response = client.post("/reports/", json=report_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == report_data["title"]
    assert data["project_id"] == project_id
    assert data["content"] == report_data["content"]


def test_get_reports(client):
    """Test getting all reports"""
    # Create project and report
    project_response = client.post("/projects/", json={"name": "Test Project", "status": "active"})
    project_id = project_response.json()["id"]
    
    report_data = {
        "project_id": project_id,
        "title": "Test Report",
        "report_type": "quarterly"
    }
    client.post("/reports/", json=report_data)
    
    response = client.get("/reports/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == report_data["title"]


def test_get_reports_by_project(client):
    """Test getting reports filtered by project"""
    # Create two projects with reports
    project1_response = client.post("/projects/", json={"name": "Project 1", "status": "active"})
    project2_response = client.post("/projects/", json={"name": "Project 2", "status": "active"})
    
    project1_id = project1_response.json()["id"]
    project2_id = project2_response.json()["id"]
    
    # Create reports for each project
    client.post("/reports/", json={"project_id": project1_id, "title": "Report 1"})
    client.post("/reports/", json={"project_id": project2_id, "title": "Report 2"})
    
    # Get reports for project 1 only
    response = client.get(f"/reports/?project_id={project1_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Report 1"
    assert data[0]["project_id"] == project1_id


def test_get_report_by_id(client):
    """Test getting a specific report"""
    # Create project and report
    project_response = client.post("/projects/", json={"name": "Test Project", "status": "active"})
    project_id = project_response.json()["id"]
    
    report_response = client.post("/reports/", json={
        "project_id": project_id,
        "title": "Test Report"
    })
    report_id = report_response.json()["id"]
    
    # Get the report
    response = client.get(f"/reports/{report_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Report"
    assert data["id"] == report_id


def test_delete_report(client):
    """Test deleting a report"""
    # Create project and report
    project_response = client.post("/projects/", json={"name": "Test Project", "status": "active"})
    project_id = project_response.json()["id"]
    
    report_response = client.post("/reports/", json={
        "project_id": project_id,
        "title": "Test Report"
    })
    report_id = report_response.json()["id"]
    
    # Delete the report
    response = client.delete(f"/reports/{report_id}")
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(f"/reports/{report_id}")
    assert get_response.status_code == 404


def test_create_report_invalid_project(client):
    """Test creating a report with invalid project_id"""
    report_data = {
        "project_id": 999,  # Non-existent project
        "title": "Test Report"
    }
    response = client.post("/reports/", json=report_data)
    assert response.status_code == 404