# Start all DEV environment resources
# Run this script at the beginning of work day

$ResourceGroup = "rg-qca-dev"
$PostgresServer = "psql-qca-dev-2f37g0"

Write-Host "🚀 Starting DEV Environment Resources..." -ForegroundColor Yellow
Write-Host ""

# Start PostgreSQL Server
Write-Host "▶️  Starting PostgreSQL Server..." -ForegroundColor Cyan
az postgres flexible-server start --resource-group $ResourceGroup --name $PostgresServer
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PostgreSQL started successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start PostgreSQL" -ForegroundColor Red
}

# Container Apps will auto-start on first request (scale-to-zero)
Write-Host ""
Write-Host "ℹ️  Container Apps will auto-start on first request" -ForegroundColor Cyan
Write-Host "   - First request may take 10-15 seconds (cold start)" -ForegroundColor Gray
Write-Host "   - Subsequent requests will be fast" -ForegroundColor Gray

Write-Host ""
Write-Host "✅ DEV Environment started!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 URLs:" -ForegroundColor Yellow
Write-Host "   Frontend: https://ca-frontend-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io" -ForegroundColor Gray
Write-Host "   API:      https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io" -ForegroundColor Gray
Write-Host "   MCP:      https://ca-mcp-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io" -ForegroundColor Gray
Write-Host ""
Write-Host "⏱️  Waiting for resources to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 30
Write-Host "✅ All resources should now be ready!" -ForegroundColor Green
