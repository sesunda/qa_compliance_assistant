# QCA Setup and Verification Guide

This document provides step-by-step instructions to set up and verify the Quantique Compliance Assistant (QCA) system.

## Prerequisites

- Docker and Docker Compose installed
- Git installed
- Ports 8000, 8001, and 5432 available

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/sesunda/qa_compliance_assistant.git
cd qa_compliance_assistant
```

### 2. Start All Services

```bash
docker compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- API service (port 8000)
- MCP Server (port 8001)

### 3. Run Database Migrations

```bash
docker compose exec -w /app/api api alembic upgrade head
```

### 4. Verify Services

Run the test script:
```bash
./test_api.sh
```

Or manually test the endpoints:

```bash
# Test API
curl http://localhost:8000/
curl http://localhost:8000/health

# Test MCP Server
curl http://localhost:8001/
curl http://localhost:8001/sample-evidence
```

## API Documentation

Once the services are running, you can access:

- **API Interactive Docs**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **MCP Server Docs**: http://localhost:8001/docs

## Example API Usage

### Create a Project

```bash
curl -X POST http://localhost:8000/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Security Compliance Project",
    "description": "Annual security compliance assessment",
    "status": "active"
  }'
```

### List All Projects

```bash
curl http://localhost:8000/projects/
```

### Create a Control

```bash
curl -X POST http://localhost:8000/controls/ \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "name": "Access Control Policy",
    "description": "Ensure proper access controls are in place",
    "control_type": "security",
    "status": "active"
  }'
```

### Create Evidence

```bash
curl -X POST http://localhost:8000/evidence/ \
  -H "Content-Type: application/json" \
  -d '{
    "control_id": 1,
    "title": "Security Audit Report",
    "description": "Q4 2024 Security Audit",
    "evidence_type": "audit_report",
    "verified": true
  }'
```

### Generate a Report

```bash
curl -X POST http://localhost:8000/reports/ \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "title": "Q4 Compliance Report",
    "content": "All controls are operational and compliant",
    "report_type": "quarterly"
  }'
```

## MCP Server Usage

### Get All Sample Evidence

```bash
curl http://localhost:8001/sample-evidence
```

### Get Sample Evidence by ID

```bash
curl http://localhost:8001/sample-evidence/1
```

### Get Sample Evidence by Type

```bash
curl http://localhost:8001/sample-evidence/type/audit_report
```

## Database Access

### Connect to PostgreSQL

```bash
docker compose exec db psql -U qca_user -d qca_db
```

### Common Database Queries

```sql
-- List all projects
SELECT * FROM projects;

-- List all controls
SELECT * FROM controls;

-- List all evidence
SELECT * FROM evidence;

-- List all reports
SELECT * FROM reports;

-- Get project with all controls
SELECT p.name as project, c.name as control 
FROM projects p 
LEFT JOIN controls c ON p.id = c.project_id;
```

## Service Management

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f mcp_server
docker compose logs -f db
```

### Stop Services

```bash
docker compose down
```

### Rebuild Services

```bash
docker compose up -d --build
```

### Reset Database

```bash
docker compose down -v
docker compose up -d
docker compose exec -w /app/api api alembic upgrade head
```

## Development

### Local Development Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install API dependencies:
```bash
cd api
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp api/.env.example api/.env
# Edit .env with your configuration
```

4. Start database only:
```bash
docker compose up -d db
```

5. Run migrations:
```bash
cd api
export PYTHONPATH=/path/to/qa_compliance_assistant
alembic upgrade head
```

6. Start API:
```bash
cd api
uvicorn api.src.main:app --reload
```

7. Start MCP Server (in new terminal):
```bash
cd mcp_server
export PYTHONPATH=/path/to/qa_compliance_assistant
uvicorn mcp_server.src.main:app --port 8001 --reload
```

## Troubleshooting

### Services won't start

Check if ports are already in use:
```bash
lsof -i :8000
lsof -i :8001
lsof -i :5432
```

### Database connection issues

Verify database is healthy:
```bash
docker compose ps
docker compose logs db
```

### Migration issues

Reset and rerun migrations:
```bash
docker compose down -v
docker compose up -d
sleep 15  # Wait for database to be ready
docker compose exec -w /app/api api alembic upgrade head
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   API Service   │────▶│   PostgreSQL    │     │   MCP Server    │
│   Port: 8000    │     │   Port: 5432    │     │   Port: 8001    │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                               │
        │                                               │
        └───────────────────┬───────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │                │
                    │  Docker Network│
                    │  qca_network   │
                    │                │
                    └────────────────┘
```

## Next Steps

1. Implement frontend application
2. Add authentication and authorization
3. Implement file upload for evidence
4. Add automated report generation
5. Implement notification system
6. Add comprehensive unit and integration tests

## Support

For issues and questions, please create an issue on the GitHub repository.
