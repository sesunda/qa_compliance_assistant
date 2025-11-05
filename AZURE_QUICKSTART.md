# Azure Deployment - Quick Start Guide

**5-Minute Setup for QA Compliance Assistant on Azure**

## Prerequisites
- ✅ Azure subscription: senthilkumar@quantiqueanalytica.com
- ✅ Azure CLI installed
- ✅ Terraform installed (v1.5+)
- ✅ Git/GitHub access

## Step 1: Azure Login (1 min)

```bash
az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

## Step 2: Create Service Principal (1 min)

**For Linux/Mac/WSL:**
```bash
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

az ad sp create-for-rbac \
  --name "qca-github-actions" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID \
  --json-auth
```

**For Windows Git Bash:**
```bash
# Use MSYS_NO_PATHCONV to prevent path mangling
MSYS_NO_PATHCONV=1 az ad sp create-for-rbac \
  --name "qca-github-actions" \
  --role contributor \
  --scopes /subscriptions/deecc652-4892-4a14-9867-151b9a6ead2b \
  --json-auth
```

**For Windows PowerShell:**
```powershell
az ad sp create-for-rbac `
  --name "qca-github-actions" `
  --role contributor `
  --scopes /subscriptions/deecc652-4892-4a14-9867-151b9a6ead2b `
  --json-auth
```

**Save the JSON output!** You'll need the `clientId`, `clientSecret`, `subscriptionId`, and `tenantId` for GitHub Secrets.

## Step 3: Configure GitHub Secrets (2 min)

Go to: `https://github.com/sesunda/qa_compliance_assistant/settings/secrets/actions`

Add these secrets from the service principal output:
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

Optional (for LLM features):
- `GROQ_API_KEY` (get free key at https://console.groq.com)

## Step 4: Configure Terraform (1 min)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars

# Edit with your Groq API key (optional)
nano terraform.tfvars
```

Minimal required changes in `terraform.tfvars`:
```hcl
groq_api_key = "your-groq-key-here"  # Optional but recommended
```

## Step 5: Deploy Infrastructure (5-10 min)

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy to Azure
terraform apply
```

Type `yes` when prompted.

## Step 6: Deploy Application (automatic)

```bash
# Push to trigger GitHub Actions deployment
git add .
git commit -m "Initial Azure deployment"
git push origin main
```

Watch deployment: https://github.com/sesunda/qa_compliance_assistant/actions

## Step 7: Post-Deployment (2 min)

```bash
# Get your API URL
terraform output api_url

# Run migrations
az containerapp exec \
  --name qca-dev-api \
  --resource-group qca-dev-rg \
  --command "alembic upgrade head"

# Seed initial data
az containerapp exec \
  --name qca-dev-api \
  --resource-group qca-dev-rg \
  --command "python -m api.scripts.seed_auth"
```

## Access Your Application

```bash
# Get all URLs
terraform output

# Open frontend
echo "Frontend: $(terraform output -raw frontend_url)"

# Open API docs
echo "API Docs: $(terraform output -raw api_url)/docs"
```

## Verify Everything Works

```bash
API_URL=$(terraform output -raw api_url)

# Test health endpoint
curl $API_URL/health

# Should return: {"status":"healthy"}
```

## 🎉 You're Done!

Your QA Compliance Assistant is now running on Azure!

- **Frontend**: https://qca-dev-frontend.{region}.azurecontainerapps.io
- **API**: https://qca-dev-api.{region}.azurecontainerapps.io/docs
- **Monitoring**: Azure Portal → Application Insights

## What's Next?

1. **Update CORS** in `api/src/config.py` with your frontend URL
2. **Set up monitoring** in Application Insights
3. **Configure backups** for PostgreSQL
4. **Review costs** in Azure Cost Management

## Troubleshooting

**Container Apps not starting?**
```bash
az containerapp logs show \
  --name qca-dev-api \
  --resource-group qca-dev-rg \
  --follow
```

**Database connection issues?**
```bash
az postgres flexible-server show \
  --name qca-dev-psql \
  --resource-group qca-dev-rg
```

**Need help?**
- See `AZURE_DEPLOYMENT.md` for detailed guide
- Check Application Insights for errors
- Review GitHub Actions logs

## Clean Up (when needed)

```bash
# Remove all Azure resources
cd terraform
terraform destroy
```

---

**Total Setup Time**: ~15 minutes  
**Monthly Cost**: ~$50-70 USD  
**Support**: senthilkumar@quantiqueanalytica.com
