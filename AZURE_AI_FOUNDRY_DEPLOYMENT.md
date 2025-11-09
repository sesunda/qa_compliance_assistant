# Azure AI Foundry - Model Deployment Guide

## 🎯 You're Already Set Up! (Almost)

You created your Azure OpenAI resource and it's showing in **Azure AI Foundry** at:
- **Project**: `qca-aoai-project`
- **Endpoint**: `https://qca-aoai.openai.azure.com/`
- **API Key**: Already generated ✅

---

## 🚀 Step-by-Step: Deploy GPT Model in Azure AI Foundry

### Step 1: Navigate to Model Catalog

From your current screen (`qca-aoai-project` overview):

1. Click **"Model catalog"** in the left sidebar
2. Search for: **"gpt-4o-mini"**
3. Click on the **"gpt-4o-mini"** model card

### Step 2: Deploy the Model

1. Click **"Deploy"** button
2. Choose deployment type: **"Standard"** (not Provisioned)
3. Configure deployment:
   ```
   Deployment name: gpt-4o-mini-deployment
   Model version: Latest (default)
   Tokens per Minute Rate Limit: 60K
   Content filter: Default
   ```
4. Click **"Deploy"**
5. Wait 1-2 minutes for deployment

### Step 3: Get Deployment Details

After deployment completes:

1. Click **"Models + endpoints"** in left sidebar (under "My assets")
2. You'll see your deployed model: `gpt-4o-mini-deployment`
3. Click on it to see details

---

## 🔑 Get Your Credentials (What You Need)

### Option A: From Azure AI Foundry Portal

You already have these visible in your screenshot:

1. **API Key**: 
   - Click the "eye" icon next to `API Key` to reveal
   - Copy the full key (starts with a long string)

2. **Endpoint**: 
   - Already shown: `https://qca-aoai.openai.azure.com/`

3. **Deployment Name**: 
   - Will be: `gpt-4o-mini-deployment` (after you deploy in steps above)

### Option B: Using Azure CLI

```powershell
# Set your resource details
$resourceGroup = "rg-qca-dev"
$accountName = "qca-aoai"

# Get endpoint
$endpoint = az cognitiveservices account show `
  --name $accountName `
  --resource-group $resourceGroup `
  --query "properties.endpoint" `
  --output tsv

Write-Host "Endpoint: $endpoint"

# Get API key
$apiKey = az cognitiveservices account keys list `
  --name $accountName `
  --resource-group $resourceGroup `
  --query "key1" `
  --output tsv

Write-Host "API Key: $apiKey"

# List deployments (after you deploy model)
az cognitiveservices account deployment list `
  --name $accountName `
  --resource-group $resourceGroup `
  --query "[].name" `
  --output table
```

---

## 📝 Summary: What You Need for Your App

After deploying the model, add these 3 environment variables to your Container App:

```
AZURE_OPENAI_ENDPOINT=https://qca-aoai.openai.azure.com/
AZURE_OPENAI_API_KEY=[copy from portal - click eye icon]
AZURE_OPENAI_MODEL=gpt-4o-mini-deployment
```

---

## 🔧 Add to Container App

### PowerShell Script:

```powershell
# Your credentials (fill these in after deploying model)
$endpoint = "https://qca-aoai.openai.azure.com/"
$apiKey = "YOUR_API_KEY_HERE"  # Get from portal
$deploymentName = "gpt-4o-mini-deployment"

# Your Container App details
$containerApp = "qa-compliance-api"
$resourceGroup = "rg-qca-dev"  # Update if different

# Update environment variables
az containerapp update `
  --name $containerApp `
  --resource-group $resourceGroup `
  --set-env-vars `
    "AZURE_OPENAI_ENDPOINT=$endpoint" `
    "AZURE_OPENAI_MODEL=$deploymentName"

# Update secret (for API key)
az containerapp update `
  --name $containerApp `
  --resource-group $resourceGroup `
  --secrets "azure-openai-api-key=$apiKey" `
  --set-env-vars "AZURE_OPENAI_API_KEY=secretref:azure-openai-api-key"

Write-Host "✅ Container App updated!"
Write-Host "Creating new revision..."

# Restart to apply changes
az containerapp revision copy `
  --name $containerApp `
  --resource-group $resourceGroup

Write-Host "✅ New revision created. Changes will apply in ~2 minutes."
```

---

## 🎯 Visual Guide: Where to Find Things in Azure AI Foundry

### Current Screen (Overview):
```
qca-aoai-project
├── Endpoints and keys ✅ (You are here)
│   ├── API Key: ••••••••••
│   └── Azure OpenAI endpoint: https://qca-aoai.openai.azure.com/
│
├── Model catalog (← Go here next)
│   └── Search "gpt-4o-mini" → Deploy
│
└── Models + endpoints (← Check after deployment)
    └── gpt-4o-mini-deployment (will appear here)
```

---

## ⚠️ Important Notes

### 1. **Model Deployment Name**
- The deployment name (`gpt-4o-mini-deployment`) is what goes in `AZURE_OPENAI_MODEL`
- NOT the model name (`gpt-4o-mini`)
- You choose this name when deploying

### 2. **Endpoint Format**
Your endpoint should look like:
```
✅ https://qca-aoai.openai.azure.com/
❌ https://qca-aoai.cognitiveservices.azure.com/  (wrong)
```

### 3. **API Version**
The app automatically uses the correct API version (`2024-02-15-preview`), so you don't need to worry about this.

---

## 🧪 Test Your Deployment

After adding credentials to Container App:

1. **Wait 2-3 minutes** for new revision to start
2. **Navigate to your app**: https://your-app.azurecontainerapps.io
3. **Go to "Agentic AI"** page (in sidebar)
4. **Test with prompt**:
   ```
   Upload 5 IM8 access control policies for project 1
   ```
5. **Check Agent Tasks** page to see progress

---

## 🆘 Troubleshooting

### "Model not found" error
**Cause**: Deployment name mismatch
**Fix**: Check deployment name in "Models + endpoints" section, update `AZURE_OPENAI_MODEL` to match exactly

### "Authentication failed" error
**Cause**: Wrong API key or endpoint
**Fix**: 
1. Click eye icon next to API Key in portal to reveal
2. Copy full key (usually 32+ characters)
3. Verify endpoint ends with `/` (slash)

### "Quota exceeded" error
**Cause**: No tokens allocated
**Fix**: 
1. Go to "Quotas" in Azure OpenAI resource
2. Request quota for Southeast Asia region
3. Allocate 60K TPM to your deployment

---

## 📚 Quick Reference

| What | Where | Value |
|------|-------|-------|
| **Endpoint** | Overview → Endpoints and keys | `https://qca-aoai.openai.azure.com/` |
| **API Key** | Overview → Endpoints and keys (click eye icon) | 32+ character string |
| **Deployment** | Model catalog → Deploy gpt-4o-mini | `gpt-4o-mini-deployment` |
| **Region** | Project details | `southeastasia` |

---

## ✅ Next Steps

1. ✅ You already created the Azure OpenAI resource
2. ⏳ **Deploy gpt-4o-mini model** (follow Step 1-2 above)
3. ⏳ **Copy API key** (click eye icon)
4. ⏳ **Update Container App** (run PowerShell script above)
5. ⏳ **Test agentic chat** (try a prompt)

---

**You're 80% done!** Just deploy the model from Model Catalog and update your Container App. 🚀
