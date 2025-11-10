# Quantique Compliance Assistant (QCA)

A comprehensive compliance management platform for Singapore IM8 and other frameworks, featuring agentic AI assistance, maker-checker workflows, and automated evidence processing.

## 🚀 Latest Updates (Nov 10, 2025)

### ✅ User Management Fix - DEPLOYED
- **Issue Fixed**: Analysts and auditors can now view the user list
- **Commit**: `46aa4c3`
- **Status**: Automatically deployed via GitHub Actions

### 🎯 IM8 Assessment Workflow - READY
- **New Feature**: Automated IM8 Excel document processing
- **Status**: Code complete, production-ready (pending Excel template creation)
- **Capabilities**: 
  - Parse IM8 Excel documents with embedded PDFs
  - Comprehensive validation (15+ rules)
  - Auto-submit to "under_review" status
  - Role-specific AI guidance

**See**: `DEPLOYMENT_STATUS.md` for current deployment details

---

## Architecture

### Production Deployment (Azure)
- **Frontend**: Azure Container Apps (React + TypeScript + Vite)
- **API**: Azure Container Apps (FastAPI + Python 3.11)
- **MCP Server**: Azure Container Apps (Model Context Protocol)
- **Database**: Azure Database for PostgreSQL
- **CI/CD**: GitHub Actions (automatic deployment on push to main)
- **Container Registry**: Azure Container Registry

### Local Development (Optional)
- Docker Compose for multi-service orchestration
- PostgreSQL database
- Volume mounts for hot-reloading

**Note**: Local Docker is resource-intensive. Use Azure deployment for testing.

---

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

### 🤖 Agentic AI Assistant
- **Multi-turn conversations** with context awareness
- **Role-specific guidance** (Admin, Auditor, Analyst, Viewer)
- **Tool calling** for compliance tasks (upload evidence, analyze gaps, generate reports)
- **File upload support** for evidence documents
- **RAG (Retrieval Augmented Generation)** for document search
- **MCP (Model Context Protocol)** integration
- **Provider support**: Groq, GitHub Models, OpenAI, Anthropic

### 📋 Compliance Management
- **Projects**: Track compliance initiatives across frameworks
- **Assessments**: IM8, ISO 27001, NIST frameworks
- **Controls**: 500+ pre-loaded controls from multiple frameworks
- **Evidence Management**: Upload, validate, and track evidence
- **Findings**: Track vulnerabilities and penetration test results
- **Maker-Checker Workflow**: Segregation of duties for evidence approval

### 🎯 IM8 Assessment Workflow (NEW)
- **Excel Template**: Structured IM8 assessment documents
- **Auto-validation**: 15+ validation rules for control IDs, statuses, embedded PDFs
- **Auto-submit**: Valid documents automatically submitted for review
- **Completion Tracking**: Real-time calculation of assessment progress
- **Role-based Prompts**: AI assistant guides auditors and analysts through workflow

### 👥 User Management
- **Role-based Access Control**: Super Admin, Admin, Auditor, Analyst, Viewer
- **Agency Isolation**: Multi-tenancy with agency-based data segregation
- **User Management UI**: Create, edit, activate/deactivate users
- **Permissions**: Granular control over resources, evidence, reports

### 📊 Dashboard & Analytics
- **Real-time Dashboards**: Control status, evidence tracking, compliance metrics
- **Gap Analysis**: AI-powered recommendations for compliance gaps
- **Custom Reports**: Generate compliance reports in multiple formats
- **Visualization**: Charts and graphs for compliance posture

### 🔄 Maker-Checker Workflow
- **Evidence Submission**: Analysts upload evidence
- **Review Process**: Auditors approve or reject with comments
- **Status Tracking**: Pending → Under Review → Approved/Rejected
- **Segregation of Duties**: Users cannot approve their own submissions

### 📁 Evidence Storage
- **Azure Blob Storage**: Scalable cloud storage for evidence files
- **Local Storage**: Fallback option for development
- **Checksum Validation**: SHA-256 checksums for file integrity
- **Metadata**: Rich metadata stored in PostgreSQL

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

## ⚠️ Security Notice

This is a development setup with the following security considerations:

- **CORS**: Currently allows all origins (*). Restrict to specific domains for production
- **Database**: Default credentials are in docker-compose.yml. Use environment variables and secrets in production
- **Authentication**: Not implemented. Add authentication/authorization before production deployment
- **HTTPS**: Not configured. Use reverse proxy (nginx/traefik) with SSL certificates in production

## Quick Start

### Production Deployment (Azure - Automatic)

**Prerequisites**: 
- Azure subscription
- GitHub repository with secrets configured

**Deployment**:
```bash
# Push to main branch - GitHub Actions handles everything
git push origin main

# Monitor deployment
# Visit: https://github.com/sesunda/qa_compliance_assistant/actions
```

**Access**:
- Frontend: `https://<your-frontend>.azurecontainerapps.io`
- API: `https://<your-api>.azurecontainerapps.io`
- API Docs: `https://<your-api>.azurecontainerapps.io/docs`

**Default Users** (created via seed script):
- Super Admin: `superadmin@example.com` / `password`
- Admin: `admin@example.com` / `password`
- Auditor: `auditor@example.com` / `password`
- Analyst: `analyst@example.com` / `password`

---

### Local Development (Optional - Resource Intensive)

**Note**: Production deployment via Azure is recommended. Local Docker is resource-intensive.

1. Clone the repository:
```bash
git clone https://github.com/sesunda/qa_compliance_assistant.git
cd qa_compliance_assistant
```

2. Start all services:
```bash
docker-compose up -d
```

3. Run migrations:
```bash
docker-compose exec api alembic upgrade head
```

4. Seed database:
```bash
docker-compose exec api python seed_agencies_users.py
```

5. Access services:
   - API: http://localhost:8000
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs

---

## 📚 Documentation

### Getting Started
- **DEPLOYMENT_STATUS.md** - Current deployment status and verification
- **QUICK_START.md** - Quick start guide for all features
- **SETUP_GUIDE.md** - Detailed setup instructions

### Feature Guides
- **USER_MANAGEMENT_FIX.md** - User management access control changes
- **IM8_QUICKSTART.md** - IM8 assessment workflow quick start
- **templates/IM8_EXCEL_TEMPLATES_README.md** - IM8 template usage guide (450+ lines)
- **AGENTIC_WORKFLOW_GUIDE.md** - Agentic AI assistant usage
- **EVIDENCE_CONTROL_MAPPING.md** - Evidence upload and control mapping

### Technical Documentation
- **PROJECT_STRUCTURE.md** - Codebase structure and organization
- **AZURE_DEPLOYMENT.md** - Azure deployment architecture
- **TESTING_GUIDE.md** - Testing procedures
- **SECURITY.md** - Security considerations

### Advanced Topics
- **MCP_IMPLEMENTATION_SUMMARY.md** - Model Context Protocol integration
- **MULTI_TURN_CONVERSATION_IMPLEMENTATION.md** - Conversation management
- **VALIDATION_PLAN.md** - Data validation architecture

---

## 🔧 API Endpoints (Production)

### Authentication
- `POST /auth/login` - User login (returns JWT token)
- `GET /auth/me` - Get current user info
- `GET /auth/users` - List users (Analyst+ access)
- `POST /auth/users` - Create user (Admin only)
- `PUT /auth/users/{id}` - Update user (Admin only)

### Projects & Assessments
- `POST /projects/` - Create compliance project
- `GET /projects/` - List projects (filtered by agency)
- `GET /projects/{id}` - Get project details
- `POST /assessments/` - Create assessment
- `GET /assessments/` - List assessments

### Controls & Evidence
- `GET /controls/` - List controls (500+ pre-loaded)
- `POST /evidence/upload` - Upload evidence (supports IM8 auto-processing)
- `POST /evidence/{id}/submit-for-review` - Submit for review
- `POST /evidence/{id}/approve` - Approve evidence (Auditor only)
- `POST /evidence/{id}/reject` - Reject evidence (Auditor only)

### Findings
- `POST /findings/` - Create finding (vulnerability/PT result)
- `GET /findings/` - List findings
- `PUT /findings/{id}` - Update finding

### Reports & Analytics
- `POST /reports/generate` - Generate compliance report
- `GET /analytics/dashboard` - Get dashboard metrics
- `POST /analytics/gap-analysis` - Run AI-powered gap analysis

### Agentic AI
- `POST /agentic/chat` - Chat with AI assistant (supports file upload)
- `GET /agentic/conversations` - List user conversations
- `POST /agentic/tasks` - Execute AI-driven compliance tasks

### Templates
- `GET /templates/evidence-upload.csv` - Download CSV template
- `GET /templates/im8-controls-sample.csv` - IM8 controls sample data

**Full API Documentation**: https://your-api-url/docs (Swagger UI)

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
# Run the API test script
./test_api.sh

# Run unit tests (once implemented)
pytest tests/ -v

# Run MCP server tests
python -m pytest tests/test_mcp_server.py -v
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