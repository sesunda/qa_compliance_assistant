# Stop all DEV environment resources to save costs
# Run this script during non-working hours (evenings, weekends)

$ResourceGroup = "rg-qca-dev"
$PostgresServer = "psql-qca-dev-2f37g0"

Write-Host "🛑 Stopping DEV Environment Resources..." -ForegroundColor Yellow
Write-Host ""

# Stop PostgreSQL Server (biggest cost saver)
Write-Host "⏸️  Stopping PostgreSQL Server..." -ForegroundColor Cyan
az postgres flexible-server stop --resource-group $ResourceGroup --name $PostgresServer
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PostgreSQL stopped successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to stop PostgreSQL" -ForegroundColor Red
}

# Container Apps will auto-scale to zero with minReplicas=0
Write-Host ""
Write-Host "ℹ️  Container Apps configured to scale to zero automatically" -ForegroundColor Cyan
Write-Host "   - API, Frontend, MCP will scale down when idle" -ForegroundColor Gray

Write-Host ""
Write-Host "✅ DEV Environment shutdown complete!" -ForegroundColor Green
Write-Host ""
Write-Host "💰 Estimated Savings:" -ForegroundColor Yellow
Write-Host "   - PostgreSQL: ~$0.10/hour = $2.40/day" -ForegroundColor Gray
Write-Host "   - Container Apps: ~$0.05/hour (when scaled to zero)" -ForegroundColor Gray
Write-Host "   - Total: ~$2.45/day when stopped" -ForegroundColor Gray
Write-Host ""
Write-Host "📅 Run start_dev_resources.ps1 to restart" -ForegroundColor Cyan
