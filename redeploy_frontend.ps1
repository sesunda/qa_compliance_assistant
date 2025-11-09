# Redeploy Frontend Container App
# This triggers a new build and deployment with latest code

$resourceGroup = "rg-qca-dev"
$frontendApp = "ca-frontend-qca-dev"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Redeploying Frontend Container App" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Creating new revision with latest code..." -ForegroundColor Yellow

# Option 1: Create new revision (triggers rebuild)
try {
    Write-Host "Triggering new frontend revision..." -ForegroundColor Gray
    az containerapp revision copy `
        --name $frontendApp `
        --resource-group $resourceGroup
    
    Write-Host "✓ New revision created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Frontend is rebuilding with latest code..." -ForegroundColor Yellow
    Write-Host "This will take about 3-5 minutes." -ForegroundColor Gray
    Write-Host ""
    Write-Host "Once complete, navigate to:" -ForegroundColor Cyan
    Write-Host "https://ca-frontend-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io/agentic-chat" -ForegroundColor Green
}
catch {
    Write-Host "✗ Failed to create new revision" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Alternative: Use Azure Portal" -ForegroundColor Yellow
    Write-Host "1. Go to portal.azure.com" -ForegroundColor Gray
    Write-Host "2. Navigate to Container Apps → $frontendApp" -ForegroundColor Gray
    Write-Host "3. Click 'Revision Management'" -ForegroundColor Gray
    Write-Host "4. Click 'Create new revision'" -ForegroundColor Gray
    Write-Host "5. Click 'Create' (keep all defaults)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
