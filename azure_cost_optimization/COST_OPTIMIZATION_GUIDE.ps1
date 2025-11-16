# Azure Cost Optimization - Scheduled Automation
# Schedule this via Windows Task Scheduler or Azure Automation

# WEEKDAY SCHEDULE (Monday-Friday)
# - Start: 8:00 AM SGT
# - Stop: 6:00 PM SGT
# Working hours: 10 hours/day = 50 hours/week
# Idle hours: 14 hours/day + 48 hours/weekend = 118 hours/week

# COST SAVINGS CALCULATION
# Assumptions (approximate):
# - PostgreSQL Burstable B1ms: $0.023/hour = $16.56/month (if running 24/7)
# - Container Apps (3 apps with scale-to-zero): $0.05/hour when active = $36/month (if running 24/7)
# - Total monthly cost (24/7): ~$52.56

# With Scheduled Shutdown (Working Hours Only):
# - Working hours: 50 hours/week * 4 weeks = 200 hours/month
# - PostgreSQL: $0.023 * 200 = $4.60/month (save $11.96 = 72%)
# - Container Apps (scale-to-zero during idle): ~$10/month (save $26 = 72%)
# - Total: ~$14.60/month (save $37.96 = 72%)

# NOTE: Resource right-sizing was tested but reverted.
# API container needs full 1Gi memory for ML model (llama-3.1-8b-instant).
# Reducing to 0.5Gi caused container health issues.
# Scale-to-zero (minReplicas=0) already provides significant cost savings during idle periods.

# IMPLEMENTATION OPTIONS:

# Option 1: Windows Task Scheduler (Local Machine)
# ------------------------------------------------
# 1. Open Task Scheduler
# 2. Create Basic Task
# 3. Start Time: 8:00 AM SGT (weekdays)
#    Action: Run PowerShell script
#    Script: C:\...\start_dev_resources.ps1
# 4. Create another task for 6:00 PM SGT
#    Script: C:\...\stop_dev_resources.ps1
# 5. Set conditions: Only run if computer is awake

# Option 2: Azure Automation Account (Cloud-Based)
# -------------------------------------------------
# 1. Create Automation Account
# 2. Create Runbook (PowerShell)
# 3. Add Azure CLI commands
# 4. Schedule: 8 AM start, 6 PM stop (Singapore Time = UTC+8)
# 5. Cost: ~$0 (500 minutes free tier)

# Option 3: GitHub Actions (CI/CD)
# ---------------------------------
# 1. Create workflow: .github/workflows/azure-cost-schedule.yml
# 2. Schedule with cron:
#    - Start: '0 0 * * 1-5'  (8 AM SGT = 0 UTC)
#    - Stop: '0 10 * * 1-5'  (6 PM SGT = 10 UTC)
# 3. Use azure/login action with service principal
# 4. Cost: $0 (GitHub Actions free for public repos)

Write-Host "📊 Azure Cost Optimization Summary" -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ Optimizations Applied:" -ForegroundColor Green
Write-Host "   1. Scale-to-Zero: minReplicas=0 for all Container Apps ✅ APPLIED" -ForegroundColor Gray
Write-Host "   2. Resource Right-Sizing: Kept original resources (API needs 1Gi for ML model)" -ForegroundColor Gray
Write-Host "   3. Scheduled Shutdown: Scripts ready for automation ✅ READY" -ForegroundColor Gray
Write-Host "   4. Model Optimization: Switched to 8B model (3-5x faster) ✅ DEPLOYED" -ForegroundColor Gray
Write-Host "   5. Image Cleanup: Removed obsolete ACR images ✅ COMPLETED" -ForegroundColor Gray
Write-Host ""
Write-Host "💰 Expected Monthly Savings:" -ForegroundColor Yellow
Write-Host "   Before: ~$52.56/month (24/7 operation)" -ForegroundColor Red
Write-Host "   After:  ~$14.60/month (scheduled operation)" -ForegroundColor Green
Write-Host "   Savings: ~$37.96/month (72% reduction) 🎉" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Test stop script: .\stop_dev_resources.ps1" -ForegroundColor Gray
Write-Host "   2. Test start script: .\start_dev_resources.ps1" -ForegroundColor Gray
Write-Host "   3. Set up automation (choose one option above)" -ForegroundColor Gray
Write-Host "   4. Monitor Azure Cost Management dashboard" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  Important Notes:" -ForegroundColor Red
Write-Host "   - PostgreSQL storage can't be decreased (Azure limitation)" -ForegroundColor Gray
Write-Host "   - First request after scale-up takes 10-15 seconds" -ForegroundColor Gray
Write-Host "   - Database connections will be lost during stop/start" -ForegroundColor Gray
Write-Host "   - Consider stopping resources during weekends for max savings" -ForegroundColor Gray
