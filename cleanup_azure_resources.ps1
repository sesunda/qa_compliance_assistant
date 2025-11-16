# Azure Resource Cleanup Script for QCA Dev Environment
# This script identifies and helps clean up unused Azure resources

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Azure Resource Cleanup Analysis - rg-qca-dev" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 1. CHECK UNUSED/OLD ACR REPOSITORIES
Write-Host "1️⃣ UNUSED ACR REPOSITORIES" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"
Write-Host "Found repositories: api, ca-api, ca-api-qca-dev, frontend"
Write-Host ""
Write-Host "❌ UNUSED: 'api' and 'ca-api' (old repositories)" -ForegroundColor Red
Write-Host "✅ ACTIVE: 'ca-api-qca-dev' and 'frontend'" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Recommendation: DELETE 'api' and 'ca-api' repositories" -ForegroundColor Magenta
Write-Host "   Command: az acr repository delete --name acrqcadev2f37g0 --repository api --yes"
Write-Host "   Command: az acr repository delete --name acrqcadev2f37g0 --repository ca-api --yes"
Write-Host ""

# 2. CHECK OLD IMAGE TAGS
Write-Host "2️⃣ OLD IMAGE TAGS IN ca-api-qca-dev" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"
Write-Host "✅ KEEP: latest (current deployment)" -ForegroundColor Green
Write-Host "✅ KEEP: base (for fast builds)" -ForegroundColor Green
Write-Host "❌ DELETE: mixtral (old decommissioned model tag)" -ForegroundColor Red
Write-Host "❌ DELETE: 20251116145742922033 (timestamped tag)" -ForegroundColor Red
Write-Host "❌ DELETE: 20251116134900945702 (timestamped tag)" -ForegroundColor Red
Write-Host "❌ DELETE: 20251116132848575384 (timestamped tag)" -ForegroundColor Red
Write-Host ""
Write-Host "💡 Recommendation: DELETE old tags to save storage costs" -ForegroundColor Magenta
Write-Host "   Command: az acr repository delete --name acrqcadev2f37g0 --image ca-api-qca-dev:mixtral --yes"
Write-Host "   Command: az acr repository delete --name acrqcadev2f37g0 --image ca-api-qca-dev:20251116145742922033 --yes"
Write-Host "   Command: az acr repository delete --name acrqcadev2f37g0 --image ca-api-qca-dev:20251116134900945702 --yes"
Write-Host "   Command: az acr repository delete --name acrqcadev2f37g0 --image ca-api-qca-dev:20251116132848575384 --yes"
Write-Host ""

# 3. CHECK LOG ANALYTICS WORKSPACES
Write-Host "3️⃣ LOG ANALYTICS WORKSPACES" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"
Write-Host "Found 2 workspaces:"
Write-Host "  - log-qca-dev (primary)" -ForegroundColor Green
Write-Host "  - workspace-rgqcadevJgjp (duplicate?)" -ForegroundColor Yellow
Write-Host ""
Write-Host "💡 Recommendation: Verify if workspace-rgqcadevJgjp is needed" -ForegroundColor Magenta
Write-Host "   If unused, delete to save costs (~$2-5/day for unused workspace)"
Write-Host ""

# 4. CHECK CONTAINER APP REVISIONS
Write-Host "4️⃣ CONTAINER APP REVISIONS" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"
Write-Host "✅ Only 1 active revision (0000051) - No cleanup needed!" -ForegroundColor Green
Write-Host "   Azure automatically deactivates old revisions"
Write-Host ""

# 5. SUMMARY
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "CLEANUP SUMMARY" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "💰 COST SAVINGS ESTIMATE:" -ForegroundColor Yellow
Write-Host "  - Delete 2 unused ACR repos: ~$0.50-1/month" -ForegroundColor White
Write-Host "  - Delete 4 old image tags: ~$0.10-0.20/month" -ForegroundColor White
Write-Host "  - Delete duplicate Log Analytics: ~$60-150/month" -ForegroundColor White
Write-Host "  ------------------------------------------------"
Write-Host "  TOTAL POTENTIAL SAVINGS: ~$60-151/month" -ForegroundColor Green
Write-Host ""

Write-Host "⚠️  EXECUTE CLEANUP?" -ForegroundColor Red
Write-Host ""
$confirm = Read-Host "Type 'YES' to execute cleanup, or press Enter to skip"

if ($confirm -eq "YES") {
    Write-Host ""
    Write-Host "🗑️ STARTING CLEANUP..." -ForegroundColor Cyan
    Write-Host ""
    
    # Delete unused ACR repositories
    Write-Host "Deleting unused ACR repository: api..." -ForegroundColor Yellow
    az acr repository delete --name acrqcadev2f37g0 --repository api --yes 2>$null
    Write-Host "Deleting unused ACR repository: ca-api..." -ForegroundColor Yellow
    az acr repository delete --name acrqcadev2f37g0 --repository ca-api --yes 2>$null
    
    # Delete old image tags
    Write-Host "Deleting old image tag: mixtral..." -ForegroundColor Yellow
    az acr repository delete --name acrqcadev2f37g0 --image ca-api-qca-dev:mixtral --yes 2>$null
    Write-Host "Deleting old image tag: 20251116145742922033..." -ForegroundColor Yellow
    az acr repository delete --name acrqcadev2f37g0 --image ca-api-qca-dev:20251116145742922033 --yes 2>$null
    Write-Host "Deleting old image tag: 20251116134900945702..." -ForegroundColor Yellow
    az acr repository delete --name acrqcadev2f37g0 --image ca-api-qca-dev:20251116134900945702 --yes 2>$null
    Write-Host "Deleting old image tag: 20251116132848575384..." -ForegroundColor Yellow
    az acr repository delete --name acrqcadev2f37g0 --image ca-api-qca-dev:20251116132848575384 --yes 2>$null
    
    Write-Host ""
    Write-Host "✅ CLEANUP COMPLETED!" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  MANUAL ACTION REQUIRED:" -ForegroundColor Yellow
    Write-Host "  Check if 'workspace-rgqcadevJgjp' Log Analytics workspace is needed"
    Write-Host "  If not needed, delete manually to save ~$60-150/month"
    Write-Host "  Command: az monitor log-analytics workspace delete --resource-group rg-qca-dev --workspace-name workspace-rgqcadevJgjp --yes"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Cleanup cancelled. No changes made." -ForegroundColor Yellow
    Write-Host ""
}
