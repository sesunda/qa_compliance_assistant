# Azure Deployment Guide

Complete guide to deploying the QA Compliance Assistant to Azure with Terraform and CI/CD.

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Initial Setup](#initial-setup)
4. [Terraform Deployment](#terraform-deployment)
5. [CI/CD Setup](#cicd-setup)
6. [Post-Deployment](#post-deployment)
7. [Troubleshooting](#troubleshooting)

## 🏗️ Architecture Overview

### Azure Resources

- **Azure Container Apps** - Hosting for API, Frontend, and MCP Server
- **Azure Database for PostgreSQL** - Flexible Server (Burstable B1ms)
- **Azure Blob Storage** - Evidence and reports storage
- **Azure Container Registry** - Private Docker image registry
- **Azure Key Vault** - Secrets management
- **Azure Application Insights** - Monitoring and logging
- **Managed Identity** - Passwordless authentication

### Infrastructure Flow

```
GitHub → GitHub Actions → ACR → Container Apps → PostgreSQL
                                 ↓
                           Azure Blob Storage
```

## 📦 Prerequisites

### Required Tools

1. **Azure CLI** (>= 2.50.0)
   ```bash
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   az --version
   ```

2. **Terraform** (>= 1.5.0)
   ```bash
   wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
   echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
   sudo apt update && sudo apt install terraform
   terraform --version
   ```

3. **Git** and **GitHub CLI** (optional)
   ```bash
   sudo apt install git gh
   ```

### Azure Subscription

- Active Azure subscription (senthilkumar@quantiqueanalytica.com)
- Contributor or Owner role on subscription

### API Keys (Optional but Recommended)

- **Groq API Key** (Free tier: 30 req/min) - https://console.groq.com
- **OpenAI API Key** (if using OpenAI)
- **Anthropic API Key** (if using Claude)

## 🚀 Initial Setup

### 1. Azure Login

```bash
# Login to Azure
az login

# Verify subscription
az account show

# Set subscription (if needed)
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

### 2. Create Service Principal for GitHub Actions

Create a service principal for GitHub Actions to authenticate with Azure:

```bash
# Create service principal
az ad sp create-for-rbac \
  --name "qca-github-actions" \
  --role contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \
  --sdk-auth

# Save the output JSON - you'll need it for GitHub Secrets
```

The output will look like:
```json
{
  "clientId": "...",
  "clientSecret": "...",
  "subscriptionId": "...",
  "tenantId": "...",
  "activeDirectoryEndpointUrl": "...",
  "resourceManagerEndpointUrl": "...",
  "activeDirectoryGraphResourceId": "...",
  "sqlManagementEndpointUrl": "...",
  "galleryEndpointUrl": "...",
  "managementEndpointUrl": "..."
}
```

### 3. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add the following secrets:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `AZURE_CLIENT_ID` | From service principal output | Client ID |
| `AZURE_TENANT_ID` | From service principal output | Tenant ID |
| `AZURE_SUBSCRIPTION_ID` | From service principal output | Subscription ID |
| `GROQ_API_KEY` | Your Groq API key | For LLM (optional) |
| `OPENAI_API_KEY` | Your OpenAI API key | For LLM (optional) |
| `ANTHROPIC_API_KEY` | Your Anthropic API key | For LLM (optional) |

### 4. Configure Terraform Variables

```bash
cd terraform

# Copy example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

**terraform.tfvars:**
```hcl
project_name = "qca"
environment  = "dev"
location     = "eastus"

postgres_admin_username = "qcaadmin"
postgres_database_name  = "qca_db"

llm_provider = "groq"  # Options: openai, groq, anthropic

# API Keys (optional - can also use GitHub Secrets)
groq_api_key      = "your-groq-api-key"
openai_api_key    = ""
anthropic_api_key = ""

tags = {
  Project     = "QA Compliance Assistant"
  Environment = "dev"
  ManagedBy   = "Terraform"
  Owner       = "senthilkumar@quantiqueanalytica.com"
}
```

## 🏗️ Terraform Deployment

### Manual Deployment (First Time)

```bash
cd terraform

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Preview changes
terraform plan

# Apply changes
terraform apply
```

Review the plan and type `yes` to proceed.

### Get Deployment Outputs

```bash
# View all outputs
terraform output

# Get specific outputs
terraform output frontend_url
terraform output api_url
terraform output postgres_fqdn

# Save outputs to JSON
terraform output -json > outputs.json
```

### Important Outputs

After deployment, note these URLs:
- **Frontend URL**: `https://qca-dev-frontend.{region}.azurecontainerapps.io`
- **API URL**: `https://qca-dev-api.{region}.azurecontainerapps.io`
- **MCP Server URL**: `https://qca-dev-mcp.{region}.azurecontainerapps.io`

## 🔄 CI/CD Setup

### Workflows Overview

Three GitHub Actions workflows are configured:

1. **terraform-plan.yml** - Runs on PRs to preview infrastructure changes
2. **terraform-apply.yml** - Applies infrastructure changes on merge to main
3. **deploy-dev.yml** - Builds and deploys application containers

### Triggering Deployments

**Infrastructure Changes:**
```bash
# Make changes to terraform/*.tf files
git add terraform/
git commit -m "Update infrastructure"
git push origin main  # Triggers terraform-apply.yml
```

**Application Changes:**
```bash
# Make changes to api/, frontend/, or mcp_server/
git add .
git commit -m "Update application"
git push origin main  # Triggers deploy-dev.yml
```

### Manual Deployment Trigger

You can also trigger deployments manually:

1. Go to GitHub → Actions → Select workflow
2. Click "Run workflow"
3. Select branch and click "Run workflow"

## 📊 Post-Deployment

### 1. Verify Container Apps

```bash
# List container apps
az containerapp list --resource-group qca-dev-rg --output table

# View specific app
az containerapp show \
  --name qca-dev-api \
  --resource-group qca-dev-rg

# View logs
az containerapp logs show \
  --name qca-dev-api \
  --resource-group qca-dev-rg \
  --follow
```

### 2. Run Database Migrations

Migrations should run automatically via GitHub Actions, but you can run manually:

```bash
az containerapp exec \
  --name qca-dev-api \
  --resource-group qca-dev-rg \
  --command "alembic upgrade head"
```

### 3. Seed Initial Data

```bash
# Seed authentication data
az containerapp exec \
  --name qca-dev-api \
  --resource-group qca-dev-rg \
  --command "python -m api.scripts.seed_auth"

# Seed controls
az containerapp exec \
  --name qca-dev-api \
  --resource-group qca-dev-rg \
  --command "python -m api.scripts.seed_controls"
```

### 4. Test API Endpoints

```bash
# Get API URL
API_URL=$(terraform output -raw api_url)

# Test health endpoint
curl $API_URL/health

# Test API docs
echo "Open: $API_URL/docs"
```

### 5. View Application Insights

```bash
# Open Application Insights in Azure Portal
az portal view \
  --resource-id $(terraform output -raw application_insights_id)
```

## 🔒 Security Considerations

### Managed Identity

All services use **Managed Identity** for passwordless authentication:
- Container Apps → Azure Blob Storage
- Container Apps → Azure Container Registry
- Container Apps → Azure Key Vault

### Secrets Management

Sensitive values are stored in:
1. **Azure Key Vault** - Database connection strings, storage keys
2. **GitHub Secrets** - API keys, service principal credentials
3. **Container App Secrets** - Runtime secrets

### Network Security

- Container Apps use **private networking** within the environment
- PostgreSQL has firewall rules (currently allows Azure services)
- Storage Account uses **private endpoints** (optional, not configured)

### CORS Configuration

Update CORS settings in `api/src/config.py`:
```python
ALLOWED_ORIGINS: List[str] = [
    "https://qca-dev-frontend.{region}.azurecontainerapps.io",
    "http://localhost:3000"  # For local development
]
```

## 🐛 Troubleshooting

### Container App Not Starting

```bash
# Check container app status
az containerapp show \
  --name qca-dev-api \
  --resource-group qca-dev-rg \
  --query "properties.runningStatus"

# View recent logs
az containerapp logs show \
  --name qca-dev-api \
  --resource-group qca-dev-rg \
  --tail 100
```

### Database Connection Issues

```bash
# Test database connectivity
az postgres flexible-server connect \
  --name qca-dev-psql \
  --admin-user qcaadmin \
  --database qca_db

# Check firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group qca-dev-rg \
  --name qca-dev-psql
```

### Blob Storage Access Issues

```bash
# Verify managed identity has access
az role assignment list \
  --assignee $(terraform output -raw managed_identity_principal_id) \
  --scope $(terraform output -raw storage_account_id)

# Test blob storage access
az storage blob list \
  --account-name $(terraform output -raw storage_account_name) \
  --container-name evidence \
  --auth-mode login
```

### GitHub Actions Failures

1. Check workflow logs in GitHub Actions tab
2. Verify GitHub Secrets are set correctly
3. Ensure service principal has correct permissions
4. Check Azure resource quotas

### View All Resource Groups

```bash
az group list --output table
```

### Clean Up Resources

```bash
# Destroy all resources (CAUTION!)
cd terraform
terraform destroy

# Or delete resource group
az group delete --name qca-dev-rg --yes --no-wait
```

## 💰 Cost Management

### Monitor Costs

```bash
# View resource group costs
az consumption usage list \
  --resource-group qca-dev-rg \
  --start-date $(date -d "30 days ago" +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d)
```

### Cost Optimization Tips

1. **Scale Down When Not in Use**:
   ```bash
   az containerapp update \
     --name qca-dev-api \
     --resource-group qca-dev-rg \
     --min-replicas 0 \
     --max-replicas 1
   ```

2. **Use B1ms PostgreSQL tier** (already configured)
3. **Use LRS storage replication** (already configured)
4. **Set up auto-shutdown schedules** (if needed)

## 📚 Additional Resources

- [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [GitHub Actions for Azure](https://github.com/Azure/actions)
- [Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)

## 🆘 Support

For issues or questions:
1. Check Application Insights logs
2. Review GitHub Actions workflow logs
3. Check Azure Portal for resource status
4. Contact: senthilkumar@quantiqueanalytica.com
