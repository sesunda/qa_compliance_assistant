# IM8 Compliance System Demo Setup Script
# This script sets up the database with IM8 framework data

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "IM8 Compliance Assistant Demo Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Seed IM8 Domain Areas
Write-Host "[1/3] Seeding IM8 Framework (10 Domain Areas)..." -ForegroundColor Yellow
try {
    python -m api.scripts.seed_im8
    Write-Host "✓ IM8 framework loaded successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Error seeding IM8 framework: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Seed Auth Data (Creates test users)
Write-Host "[2/3] Creating test users (Analysts, Auditors, Viewers)..." -ForegroundColor Yellow
try {
    python -m api.scripts.seed_auth
    Write-Host "✓ Users created successfully" -ForegroundColor Green
    Write-Host "  - admin@quantique.sg (Admin)" -ForegroundColor Gray
    Write-Host "  - analyst@quantique.sg (Analyst)" -ForegroundColor Gray
    Write-Host "  - auditor@quantique.sg (Auditor)" -ForegroundColor Gray
    Write-Host "  - viewer@quantique.sg (Viewer)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Error creating users: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 3: Information about next steps
Write-Host "[3/3] System ready!" -ForegroundColor Green
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Login to the application:" -ForegroundColor White
Write-Host "   URL: https://ca-app-qca-dev-victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io" -ForegroundColor Gray
Write-Host "   User: admin@quantique.sg" -ForegroundColor Gray
Write-Host "   Pass: SecurePass123!" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Navigate to 'AI Assistant' in the sidebar" -ForegroundColor White
Write-Host ""
Write-Host "3. Try these prompts:" -ForegroundColor White
Write-Host ""
Write-Host "   📋 Create Assessment:" -ForegroundColor Yellow
Write-Host '   "Create a new IM8 compliance assessment for Q4 2025 covering all production systems"' -ForegroundColor Gray
Write-Host ""
Write-Host "   🛡️ Upload Controls:" -ForegroundColor Yellow
Write-Host '   "Upload 30 IM8 controls covering all 10 domain areas (Access Control, Network Security,' -ForegroundColor Gray
Write-Host '   Data Protection, etc). Include implementation guidance and evidence requirements."' -ForegroundColor Gray
Write-Host ""
Write-Host "   📄 Upload Evidence:" -ForegroundColor Yellow
Write-Host '   "I have access control policies in /storage/evidence/policies/. Analyze them and' -ForegroundColor Gray
Write-Host '   map to IM8-01 controls. Mark as pending review."' -ForegroundColor Gray
Write-Host ""
Write-Host "   🔍 Import Findings:" -ForegroundColor Yellow
Write-Host '   "Import findings from our VAPT report: SQL injection (critical), XSS (high),' -ForegroundColor Gray
Write-Host '   missing security headers (medium). Map to IM8-03 Application Security controls."' -ForegroundColor Gray
Write-Host ""
Write-Host "   📊 Generate Report:" -ForegroundColor Yellow
Write-Host '   "Generate an executive compliance report with overall score, findings summary,' -ForegroundColor Gray
Write-Host '   and recommendations."' -ForegroundColor Gray
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📖 Complete Workflow Guide: AGENTIC_WORKFLOW_GUIDE.md" -ForegroundColor White
Write-Host "📁 Templates: templates/ directory" -ForegroundColor White
Write-Host "🔧 API Docs: /docs endpoint" -ForegroundColor White
Write-Host ""
Write-Host "✨ The system is now ready for agentic AI operations!" -ForegroundColor Green
Write-Host ""
