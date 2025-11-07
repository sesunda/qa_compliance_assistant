# Azure-Only Migration Guide

## 🎯 Objective
Transition from Codespaces + Azure to **Azure-only** deployment to avoid double expenditure.

## ✅ Current Status
- **Codespaces Dependencies**: ✅ REMOVED (minimal impact)
- **Azure Infrastructure**: ✅ READY (Terraform configured)
- **CI/CD Pipelines**: ✅ CONFIGURED (GitHub Actions)
- **Application Code**: ✅ CONTAINERIZED

## 🚀 Immediate Steps

### 1. Verify Azure CLI Setup
```powershell
# Check if Azure CLI is installed
az --version

# Login to Azure
az login

# Verify subscription
az account show

# Set subscription if needed
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

### 2. Configure GitHub Secrets (If Not Already Done)

Go to GitHub Repository → Settings → Secrets and variables → Actions

Required secrets:
- `AZURE_CLIENT_ID` - Service principal client ID
- `AZURE_TENANT_ID` - Azure tenant ID  
- `AZURE_SUBSCRIPTION_ID` - Azure subscription ID
- `GROQ_API_KEY` - For free LLM (optional)

### 3. Deploy Infrastructure
```powershell
cd terraform

# Copy and configure variables
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values:
# - project_name = "qca"
# - environment = "dev" 
# - location = "eastus"
# - postgres_admin_username = "qcaadmin"
# - groq_api_key = "your-groq-key" (optional)

# Initialize and deploy
terraform init
terraform plan
terraform apply
```

### 4. Push Code to Trigger Deployment
```powershell
git add .
git commit -m "Azure-only deployment ready"
git push origin main
```

This will trigger GitHub Actions to:
- Build Docker images
- Push to Azure Container Registry
- Deploy to Azure Container Apps
- Run database migrations

### 5. Access Your Application

After deployment completes (5-10 minutes):

```powershell
# Get URLs from Terraform
cd terraform
terraform output

# Your application will be available at:
# - Frontend: https://ca-frontend-qca-dev.{region}.azurecontainerapps.io
# - API: https://ca-api-qca-dev.{region}.azurecontainerapps.io/docs
# - MCP Server: https://ca-mcp-qca-dev.{region}.azurecontainerapps.io/docs
```

## 💰 Cost Optimization Benefits

### Before (Codespaces + Azure):
- **Codespaces**: ~$0.18/hour when active
- **Azure**: Container Apps + PostgreSQL ~$30-50/month
- **Total**: $50-80/month (if Codespaces used regularly)

### After (Azure Only):
- **Azure**: Container Apps + PostgreSQL ~$30-50/month
- **Development**: Use local Docker Compose
- **Total**: $30-50/month (**40-60% cost savings**)

## 🔧 Local Development Setup

Instead of Codespaces, use local development:

```powershell
# Clone repository
git clone https://github.com/sesunda/qa_compliance_assistant.git
cd qa_compliance_assistant

# Start local environment
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head

# Access locally:
# - Frontend: http://localhost:3000
# - API: http://localhost:8000/docs
# - MCP Server: http://localhost:8001/docs
```

## 🎛️ Scale to Zero for Cost Savings

Azure Container Apps can scale to zero when not in use:

```bash
# Already configured in terraform/main.tf:
# - Frontend: min_replicas = 0
# - MCP Server: min_replicas = 0  
# - API: min_replicas = 1 (keeps one instance)
```

## 📊 Monitoring & Management

Access via Azure Portal:
- **Resource Group**: `rg-qca-dev`
- **Container Apps**: Monitor scaling and logs
- **PostgreSQL**: Database metrics
- **Storage Account**: Evidence and reports
- **Application Insights**: Performance monitoring

## 🚨 Emergency Rollback

If needed, you can still run locally:
```powershell
docker-compose up -d
```

## ✅ Migration Complete Checklist

- [ ] Removed Codespaces references from code
- [ ] Configured GitHub Secrets for Azure
- [ ] Deployed infrastructure with Terraform
- [ ] Verified application is running on Azure
- [ ] Tested all endpoints work
- [ ] Disabled/deleted any Codespaces instances
- [ ] Updated team about new development workflow

## 📞 Support

If issues occur:
1. Check GitHub Actions logs
2. Review Azure Container Apps logs
3. Contact: senthilkumar@quantiqueanalytica.com