# QCA Project Structure

```
qa_compliance_assistant/
│
├── api/                                # FastAPI API Service
│   ├── src/
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── projects.py            # Project CRUD endpoints
│   │   │   ├── controls.py            # Control CRUD endpoints
│   │   │   ├── evidence.py            # Evidence CRUD endpoints
│   │   │   └── reports.py             # Report CRUD endpoints
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app initialization
│   │   ├── config.py                  # Configuration settings
│   │   ├── database.py                # Database connection
│   │   ├── models.py                  # SQLAlchemy models
│   │   └── schemas.py                 # Pydantic schemas
│   ├── alembic/                       # Database migrations
│   │   ├── versions/
│   │   │   └── 001_initial_migration.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini                    # Alembic configuration
│   ├── Dockerfile                     # API service container
│   ├── requirements.txt               # Python dependencies
│   └── .env.example                   # Environment variables template
│
├── mcp_server/                        # MCP Server Service
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                    # MCP FastAPI app
│   │   └── sample_data.py             # Sample evidence data
│   ├── Dockerfile                     # MCP service container
│   └── requirements.txt               # Python dependencies
│
├── frontend/                          # Future frontend application
│   └── README.md
│
├── libs/                              # Shared libraries
│   └── README.md
│
├── reports/                           # Generated reports storage
│   └── README.md
│
├── docker-compose.yml                 # Multi-service orchestration
├── .gitignore                         # Git ignore patterns
├── README.md                          # Main project documentation
├── SETUP_GUIDE.md                     # Detailed setup instructions
└── test_api.sh                        # API test script
```

## Service Ports

- **API Service**: http://localhost:8000
  - Main API: `/`
  - Health: `/health`
  - Docs: `/docs`
  - OpenAPI: `/openapi.json`

- **MCP Server**: http://localhost:8001
  - Main: `/`
  - Sample Evidence: `/sample-evidence`
  - Docs: `/docs`

- **PostgreSQL**: localhost:5432
  - Database: qca_db
  - User: qca_user
  - Password: qca_password

## Database Schema

### projects
- id (PK)
- name
- description
- status
- created_at
- updated_at

### controls
- id (PK)
- project_id (FK → projects.id)
- name
- description
- control_type
- status
- created_at
- updated_at

### evidence
- id (PK)
- control_id (FK → controls.id)
- title
- description
- file_path
- evidence_type
- verified
- created_at
- updated_at

### reports
- id (PK)
- project_id (FK → projects.id)
- title
- content
- report_type
- generated_at
- file_path

## API Endpoints

### Projects
- `POST /projects/` - Create project
- `GET /projects/` - List projects
- `GET /projects/{id}` - Get project
- `PUT /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project

### Controls
- `POST /controls/` - Create control
- `GET /controls/?project_id={id}` - List controls
- `GET /controls/{id}` - Get control
- `PUT /controls/{id}` - Update control
- `DELETE /controls/{id}` - Delete control

### Evidence
- `POST /evidence/` - Create evidence
- `GET /evidence/?control_id={id}` - List evidence
- `GET /evidence/{id}` - Get evidence
- `PUT /evidence/{id}` - Update evidence
- `DELETE /evidence/{id}` - Delete evidence

### Reports
- `POST /reports/` - Create report
- `GET /reports/?project_id={id}` - List reports
- `GET /reports/{id}` - Get report
- `DELETE /reports/{id}` - Delete report

## MCP Server Endpoints

- `GET /sample-evidence` - Get all sample evidence
- `GET /sample-evidence/{id}` - Get sample evidence by ID
- `GET /sample-evidence/type/{type}` - Get sample evidence by type

## Import Structure

All imports use the `PYTHONPATH=/app` convention:

```python
# API imports
from api.src.config import settings
from api.src.database import get_db
from api.src.models import Project, Control, Evidence, Report
from api.src.schemas import ProjectCreate, ProjectUpdate
from api.src.routers import projects, controls, evidence, reports

# MCP Server imports
from mcp_server.src.sample_data import SampleEvidence, SAMPLE_EVIDENCE
```

## Docker Volumes

- `postgres_data` - PostgreSQL data persistence
- `./api:/app/api` - API hot reload
- `./mcp_server:/app/mcp_server` - MCP Server hot reload
- `./libs:/app/libs` - Shared libraries
- `./reports:/app/reports` - Generated reports

## Environment Variables

### API Service
- `DATABASE_URL` - PostgreSQL connection string
- `API_TITLE` - API title
- `API_VERSION` - API version
- `PYTHONPATH` - Python module path

### All Services
- `PYTHONPATH=/app` - Set in docker-compose.yml
