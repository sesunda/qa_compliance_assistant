# Local Development Guide

This guide explains how to develop locally and deploy to Azure only when you choose.

## 🏠 Local Development Workflow

### 1. Run Services Locally

```bash
# Start all services with Docker Compose
docker-compose up -d

# Or run individually:
docker-compose up api      # API on http://localhost:8000
docker-compose up frontend # Frontend on http://localhost:5173
docker-compose up mcp_server # MCP Server on http://localhost:8002
```

### 2. Develop Freely

- Make changes to your code
- Test locally with Docker Compose
- Push commits to GitHub **without triggering deployment**
- Work on feature branches for isolation

### 3. Deploy to Azure (When Ready)

**Option A: Manual Trigger via GitHub UI**
1. Go to https://github.com/sesunda/qa_compliance_assistant/actions
2. Click "Deploy to Azure DEV" workflow
3. Click "Run workflow" button
4. Select branch (usually `main`)
5. Click green "Run workflow" button

**Option B: Using Git Tags (Recommended for Releases)**
```bash
# Create a release tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Then manually trigger deployment via GitHub UI
```

**Option C: Re-enable Auto-Deploy (if needed)**
Edit `.github/workflows/deploy-dev.yml` and uncomment the `push:` trigger:
```yaml
on:
  push:
    branches:
      - main
  workflow_dispatch:
```

## 💰 Cost Optimization

### Scale-to-Zero Configuration

Container Apps are configured with `min_replicas = 0`:
- **When idle**: Apps scale to zero = **$0 cost**
- **When accessed**: Apps wake up automatically (cold start ~5-10 seconds)
- **Under load**: Auto-scales up to max replicas

### Cost-Saving Tips

1. **Use scale-to-zero for DEV** (already configured)
2. **Stop database when not needed**:
   ```powershell
   # Stop PostgreSQL
   az postgres flexible-server stop --name <server-name> --resource-group rg-qca-dev
   
   # Start PostgreSQL
   az postgres flexible-server start --name <server-name> --resource-group rg-qca-dev
   ```

3. **Delete DEV environment when on vacation**:
   ```powershell
   # Delete everything
   az group delete --name rg-qca-dev --yes
   
   # Recreate when back
   cd terraform
   terraform apply
   ```

4. **Monitor costs**:
   - Azure Portal → Cost Management
   - Set budget alerts

## 🔧 Local Environment Setup

### Prerequisites

- Docker Desktop
- VS Code with Dev Containers extension
- Git

### First Time Setup

```bash
# Clone repository
git clone https://github.com/sesunda/qa_compliance_assistant.git
cd qa_compliance_assistant

# Open in VS Code Dev Container
code .
# Click "Reopen in Container" when prompted

# Copy environment file
cp .env.example .env

# Update .env with your settings
# DATABASE_URL=postgresql://user:pass@localhost:5432/qca_db
# GROQ_API_KEY=your_key_here

# Start services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head

# Seed data
docker-compose exec api python -m api.scripts.seed_auth
```

### Daily Development

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api      # API logs
docker-compose logs -f frontend # Frontend logs

# Stop services
docker-compose down
```

## 🚀 Deployment Frequency Recommendations

### DEV Environment
- **Frequency**: As needed (manual trigger)
- **When**: After completing features, before demos, for testing
- **Cost**: Minimal with scale-to-zero

### Future STAGING/PROD Environments
- **STAGING**: Auto-deploy on merge to `develop` branch
- **PROD**: Manual deployment with approval gates

## 🔄 Branching Strategy

```
main (production-ready)
  ├── develop (integration branch)
  │   ├── feature/user-management
  │   ├── feature/compliance-reports
  │   └── bugfix/login-issue
  └── hotfix/critical-security
```

**Workflow:**
1. Create feature branch: `git checkout -b feature/my-feature`
2. Develop and test locally
3. Push to GitHub: `git push origin feature/my-feature`
4. Create Pull Request to `main`
5. After PR merge, manually trigger deployment

## 📊 Monitoring Deployed Apps

```powershell
# Get app URLs
az containerapp list --resource-group rg-qca-dev --query "[].{Name:name, URL:properties.configuration.ingress.fqdn}" -o table

# Check app status
az containerapp show --name ca-api-qca-dev --resource-group rg-qca-dev --query "properties.{Status:provisioningState, Replicas:template.containers[0].resources}" -o json

# View logs
az containerapp logs show --name ca-api-qca-dev --resource-group rg-qca-dev --tail 50

# Force scale up (if needed)
az containerapp revision set-mode --name ca-api-qca-dev --resource-group rg-qca-dev --mode Single
```

## ❓ FAQ

**Q: Why doesn't my push to GitHub deploy automatically anymore?**
A: Automatic deployment is disabled. Use manual trigger via GitHub Actions UI.

**Q: How much does it cost when scale-to-zero?**
A: $0 when idle. You only pay when apps are running (handling requests).

**Q: How do I test before deploying?**
A: Run locally with `docker-compose up` and test thoroughly before manual deployment.

**Q: Can I deploy specific services only?**
A: Yes, modify the workflow or use Terraform to target specific resources.

**Q: What if I want auto-deploy back?**
A: Uncomment the `push:` trigger in `.github/workflows/deploy-dev.yml`
