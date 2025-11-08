# IM8 Compliance System Demo Setup Script
# This script sets up the database with IM8 framework data

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "IM8 Compliance Assistant Demo Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Seed IM8 Domain Areas
Write-Host "[1/2] Seeding IM8 Framework (10 Domain Areas)..." -ForegroundColor Yellow
python -m api.scripts.seed_im8
if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: IM8 framework loaded" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to seed IM8 framework" -ForegroundColor Red
}
Write-Host ""

# Step 2: Seed Auth Data (Creates test users)
Write-Host "[2/2] Creating test users..." -ForegroundColor Yellow
python -m api.scripts.seed_auth
if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: Users created" -ForegroundColor Green
    Write-Host "  - admin@quantique.sg (Admin)" -ForegroundColor Gray
    Write-Host "  - analyst@quantique.sg (Analyst)" -ForegroundColor Gray
    Write-Host "  - auditor@quantique.sg (Auditor)" -ForegroundColor Gray
    Write-Host "  - viewer@quantique.sg (Viewer)" -ForegroundColor Gray
} else {
    Write-Host "ERROR: Failed to create users" -ForegroundColor Red
}
Write-Host ""

# Information about next steps
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "SYSTEM READY!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor White
Write-Host ""
Write-Host "1. Login to the application:" -ForegroundColor Yellow
Write-Host "   URL: https://ca-app-qca-dev-victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io" -ForegroundColor Gray
Write-Host "   User: admin@quantique.sg" -ForegroundColor Gray
Write-Host "   Pass: SecurePass123!" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Navigate to 'AI Assistant' in the sidebar" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Try these example prompts:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   Create Assessment:" -ForegroundColor White
Write-Host '   "Create a new IM8 compliance assessment for Q4 2025"' -ForegroundColor Gray
Write-Host ""
Write-Host "   Upload Controls:" -ForegroundColor White
Write-Host '   "Upload 30 IM8 controls covering all 10 domain areas"' -ForegroundColor Gray
Write-Host ""
Write-Host "   Import Findings:" -ForegroundColor White
Write-Host '   "Create security findings: SQL injection, XSS, weak passwords"' -ForegroundColor Gray
Write-Host ""
Write-Host "   Generate Report:" -ForegroundColor White
Write-Host '   "Generate executive compliance report for assessment 1"' -ForegroundColor Gray
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Documentation:" -ForegroundColor White
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Complete Guide: AGENTIC_WORKFLOW_GUIDE.md" -ForegroundColor Gray
Write-Host "  Quick Start: QUICK_START.md" -ForegroundColor Gray
Write-Host "  Templates: templates/ directory" -ForegroundColor Gray
Write-Host "  API Docs: /docs endpoint" -ForegroundColor Gray
Write-Host ""
Write-Host "The system is ready for agentic AI operations!" -ForegroundColor Green
Write-Host ""
