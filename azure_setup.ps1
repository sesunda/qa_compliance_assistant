# Azure Post-Deployment Setup Script
# Run this script on Windows PowerShell after initial deployment

$RESOURCE_GROUP = "rg-qca-dev"
$API_APP = "ca-api-qca-dev"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Azure QCA Post-Deployment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Run Database Migrations
Write-Host "Step 1: Running database migrations..." -ForegroundColor Yellow
Write-Host "This will create all database tables and schema" -ForegroundColor Gray
Write-Host ""

try {
    az containerapp exec `
        --name $API_APP `
        --resource-group $RESOURCE_GROUP `
        --command "alembic upgrade head"
    
    Write-Host "✓ Database migrations completed successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Migration failed. The API container might not be running yet." -ForegroundColor Red
    Write-Host "  Wait 1 minute for the app to start, then try again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Step 2: Seed Authentication Data
Write-Host "Step 2: Seeding authentication data..." -ForegroundColor Yellow
Write-Host "This will create default users and agencies" -ForegroundColor Gray
Write-Host ""

try {
    az containerapp exec `
        --name $API_APP `
        --resource-group $RESOURCE_GROUP `
        --command "python -m api.scripts.seed_auth"
    
    Write-Host "✓ Authentication data seeded successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Seeding failed" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Seed Control Framework Data
Write-Host "Step 3: Seeding control framework data..." -ForegroundColor Yellow
Write-Host "This will create compliance controls and frameworks" -ForegroundColor Gray
Write-Host ""

try {
    az containerapp exec `
        --name $API_APP `
        --resource-group $RESOURCE_GROUP `
        --command "python -m api.scripts.seed_controls"
    
    Write-Host "✓ Control framework data seeded successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠ Control seeding failed (optional)" -ForegroundColor Yellow
}

Write-Host ""

# Display Application URLs
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Application URLs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$apps = az containerapp list --resource-group $RESOURCE_GROUP --query "[].{Name:name, URL:properties.configuration.ingress.fqdn}" -o json | ConvertFrom-Json

foreach ($app in $apps) {
    $url = "https://$($app.URL)"
    Write-Host "$($app.Name):" -ForegroundColor White
    Write-Host "  $url" -ForegroundColor Cyan
    
    if ($app.Name -like "*api*") {
        Write-Host "  API Docs: $url/docs" -ForegroundColor Gray
        Write-Host "  Health: $url/health" -ForegroundColor Gray
    }
    Write-Host ""
}

# Display Default Credentials
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Default Login Credentials" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Admin User:" -ForegroundColor Yellow
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin123" -ForegroundColor White
Write-Host ""
Write-Host "Agency Admin User:" -ForegroundColor Yellow
Write-Host "  Username: alice_admin" -ForegroundColor White
Write-Host "  Password: password123" -ForegroundColor White
Write-Host ""
Write-Host "Agency User:" -ForegroundColor Yellow
Write-Host "  Username: bob_user" -ForegroundColor White
Write-Host "  Password: password123" -ForegroundColor White
Write-Host ""

Write-Host "⚠ IMPORTANT: Change these default passwords in production!" -ForegroundColor Red
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Update CORS configuration in api/src/config.py" -ForegroundColor White
Write-Host "2. Add your frontend URL to ALLOWED_ORIGINS" -ForegroundColor White
Write-Host "3. Redeploy the API with updated CORS settings" -ForegroundColor White
Write-Host "4. Access the frontend and login with default credentials" -ForegroundColor White
Write-Host ""

Write-Host "Setup completed successfully! 🎉" -ForegroundColor Green
