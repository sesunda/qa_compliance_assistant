# Fast Build Script - Uses Pre-built Base Image
# This builds in ~2-3 minutes in ACR

$imageName = "qca-backend:evidence-indexing"

Write-Host "Building $imageName using fast Dockerfile..." -ForegroundColor Green
Write-Host "This should complete in 2-3 minutes." -ForegroundColor Yellow

az acr build --registry acrqcadev2f37g0 `
  --image $imageName `
  --file api/Dockerfile.fast .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Fast build completed successfully!" -ForegroundColor Green
Write-Host "`nTo deploy to Container Apps, run:" -ForegroundColor Yellow
Write-Host "az containerapp update --name ca-api-qca-dev --resource-group rg-qca-dev --image acrqcadev2f37g0.azurecr.io/$imageName" -ForegroundColor Cyan
