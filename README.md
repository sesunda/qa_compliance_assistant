# Quantique Compliance Assistant (QCA)

A multi-service FastAPI project for managing compliance, controls, evidence, and reporting.

## Project Structure

```
qa_compliance_assistant/
├── api/                  # FastAPI API service
│   ├── src/
│   │   ├── routers/      # API route handlers
│   │   ├── models.py     # SQLAlchemy models
│   │   ├── schemas.py    # Pydantic schemas
│   │   ├── database.py   # Database configuration
│   │   ├── config.py     # Application settings
│   │   └── main.py       # FastAPI application
│   ├── alembic/          # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── mcp_server/           # MCP Server - Sample Evidence Provider
│   ├── src/
│   │   ├── sample_data.py
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # Future frontend application
├── libs/                 # Shared libraries
├── reports/              # Generated reports storage
└── docker-compose.yml    # Multi-service orchestration
```

## Features

### API Service
- **Projects**: Manage compliance projects
- **Controls**: Define and track compliance controls
- **Evidence**: Store and manage evidence for controls
- **Reports**: Generate compliance reports

### MCP Server
- Provides sample evidence data
- RESTful API for accessing sample evidence

### Database
- PostgreSQL database for persistent storage
- Alembic migrations for schema management

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

## Getting Started

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/sesunda/qa_compliance_assistant.git
cd qa_compliance_assistant
```

2. Start all services:
```bash
docker-compose up -d
```

3. Wait for services to be healthy, then run migrations:
```bash
docker-compose exec api alembic upgrade head
```

4. Access the services:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - MCP Server: http://localhost:8001
   - MCP Server Docs: http://localhost:8001/docs
   - PostgreSQL: localhost:5432

### Local Development

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
cp .env.example .env
# Edit .env with your configuration
```

4. Start PostgreSQL (using Docker):
```bash
docker-compose up -d db
```

5. Run migrations:
```bash
cd api
alembic upgrade head
```

6. Start the API service:
```bash
export PYTHONPATH=/path/to/qa_compliance_assistant
cd api
uvicorn api.src.main:app --reload
```

7. Start the MCP Server (in a new terminal):
```bash
export PYTHONPATH=/path/to/qa_compliance_assistant
cd mcp_server
uvicorn mcp_server.src.main:app --port 8001 --reload
```

## API Endpoints

### Projects
- `POST /projects/` - Create a new project
- `GET /projects/` - List all projects
- `GET /projects/{id}` - Get a specific project
- `PUT /projects/{id}` - Update a project
- `DELETE /projects/{id}` - Delete a project

### Controls
- `POST /controls/` - Create a new control
- `GET /controls/` - List all controls (filter by project_id)
- `GET /controls/{id}` - Get a specific control
- `PUT /controls/{id}` - Update a control
- `DELETE /controls/{id}` - Delete a control

### Evidence
- `POST /evidence/` - Create new evidence
- `GET /evidence/` - List all evidence (filter by control_id)
- `GET /evidence/{id}` - Get specific evidence
- `PUT /evidence/{id}` - Update evidence
- `DELETE /evidence/{id}` - Delete evidence

### Reports
- `POST /reports/` - Create a new report
- `GET /reports/` - List all reports (filter by project_id)
- `GET /reports/{id}` - Get a specific report
- `DELETE /reports/{id}` - Delete a report

## MCP Server Endpoints

- `GET /sample-evidence` - Get all sample evidence
- `GET /sample-evidence/{id}` - Get sample evidence by ID
- `GET /sample-evidence/type/{type}` - Get sample evidence by type

## Database Schema

### Projects
- id, name, description, status, created_at, updated_at

### Controls
- id, project_id, name, description, control_type, status, created_at, updated_at

### Evidence
- id, control_id, title, description, file_path, evidence_type, verified, created_at, updated_at

### Reports
- id, project_id, title, content, report_type, generated_at, file_path

## Environment Variables

### API Service
- `DATABASE_URL` - PostgreSQL connection string
- `API_TITLE` - API title (default: Quantique Compliance Assistant API)
- `API_VERSION` - API version (default: 1.0.0)

### Docker Environment
- `PYTHONPATH=/app` - Set automatically in containers

## Development

### Running Tests
```bash
# TODO: Add tests
```

### Adding New Migrations
```bash
cd api
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Stopping Services
```bash
docker-compose down
```

### Viewing Logs
```bash
docker-compose logs -f api
docker-compose logs -f mcp_server
docker-compose logs -f db
```

## Technologies Used

- **FastAPI** - Modern web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **PostgreSQL** - Relational database
- **Alembic** - Database migration tool
- **Pydantic** - Data validation using Python type hints
- **Docker** - Containerization platform
- **Uvicorn** - ASGI server

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.