# Build Base Image Locally and Push to ACR
# Run this script after starting Docker Desktop

Write-Host "Step 1: Building base image locally (this will take 20-30 minutes)..." -ForegroundColor Green
docker build -t acrqcadev2f37g0.azurecr.io/qca-base:v1 -f api/Dockerfile.base .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`nStep 2: Logging into ACR..." -ForegroundColor Green
az acr login --name acrqcadev2f37g0

if ($LASTEXITCODE -ne 0) {
    Write-Host "ACR login failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`nStep 3: Pushing base image to ACR..." -ForegroundColor Green
docker push acrqcadev2f37g0.azurecr.io/qca-base:v1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Push failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ SUCCESS! Base image built and pushed to ACR" -ForegroundColor Green
Write-Host "`nNow you can use fast builds with:" -ForegroundColor Yellow
Write-Host "az acr build --registry acrqcadev2f37g0 --image qca-backend:evidence-indexing --file api/Dockerfile.fast ." -ForegroundColor Cyan
