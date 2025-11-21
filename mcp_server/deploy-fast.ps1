# Fast MCP Server Deployment Script
# Uses Dockerfile.fast for rapid builds (~30 seconds)

param(
    [string]$Version = "latest"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Fast MCP Server Build & Deploy (v$Version)" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

# Step 1: Fast build using Dockerfile.fast
Write-Host "📦 Building MCP server image (fast mode)..." -ForegroundColor Yellow
az acr build `
    --registry acrqcadev2f37g0 `
    --image "qca-mcp:$Version" `
    --file Dockerfile.fast `
    .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

# Step 2: Deploy to Container App
Write-Host "`n🚢 Deploying to Azure Container App..." -ForegroundColor Yellow
az containerapp update `
    --name ca-mcp-qca-dev `
    --resource-group rg-qca-dev `
    --image "acrqcadev2f37g0.azurecr.io/qca-mcp:$Version"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ MCP Server deployed successfully!" -ForegroundColor Green
Write-Host "🔗 URL: https://ca-mcp-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io" -ForegroundColor Cyan
