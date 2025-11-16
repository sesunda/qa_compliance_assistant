# QA Compliance Assistant - Docker Build Strategy

## Image Tags Overview
- `base` - Base image with all dependencies (3.5GB), rebuild only when requirements.txt changes
- `latest` - Current production image with latest code
- `mixtral` - Old attempt with decommissioned Mixtral model (deprecated)
- Timestamped tags - Automatic builds from Azure

## Two-Stage Build Strategy

### Stage 1: Build Base Image (ONE TIME - 20 minutes)
Build the base image with all heavy dependencies pre-installed:

```powershell
cd api
az acr build --registry acrqcadev2f37g0 --image ca-api-qca-dev:base --file Dockerfile.base .
```

**When to rebuild base:**
- Only when `requirements.txt` changes
- This installs: torch (900MB), CUDA libraries (2.5GB), transformers, etc.

### Stage 2: Build Application Image (FAST - 2 minutes)
Use the base image for quick application deployments:

```powershell
cd api
az acr build --registry acrqcadev2f37g0 --image ca-api-qca-dev:latest --file Dockerfile.fast .
```

**When to use:**
- Every code change
- Only copies application files (fast!)
- Dependencies already in base image

## Deployment Commands

### Deploy with Fast Build
```powershell
# Build and deploy in one command
cd api
az acr build --registry acrqcadev2f37g0 --image ca-api-qca-dev:latest --file Dockerfile.fast .

# Update container app
az containerapp update --name ca-api-qca-dev --resource-group rg-qca-dev --image acrqcadev2f37g0.azurecr.io/ca-api-qca-dev:latest
```

### Update Dependencies (Rare)
```powershell
# 1. Rebuild base image (20 min)
cd api
az acr build --registry acrqcadev2f37g0 --image ca-api-qca-dev:base --file Dockerfile.base .

# 2. Rebuild app with new base (2 min)
az acr build --registry acrqcadev2f37g0 --image ca-api-qca-dev:latest --file Dockerfile.fast .

# 3. Deploy
az containerapp update --name ca-api-qca-dev --resource-group rg-qca-dev --image acrqcadev2f37g0.azurecr.io/ca-api-qca-dev:latest
```

## Benefits
- **90% faster** deployments (2 min vs 20 min)
- **Cheaper** - less build time = less compute cost
- **Efficient** - dependencies cached in base image
- **Flexible** - easy to update code without reinstalling 3.5GB of dependencies

## Current Issue
The ongoing build is using the old `Dockerfile` which reinstalls everything. Let it complete this time, then switch to the fast build strategy for future deployments.
