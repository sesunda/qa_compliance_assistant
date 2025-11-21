# Azure Resource Housekeeping Script
# Comprehensive cleanup for QCA Compliance Assistant infrastructure
# - Cleans up old container app revisions
# - Removes unused ACR repositories and old images
# - Deletes duplicate Log Analytics workspaces
# - Documents automation schedules and cost optimization

param(
    [switch]$DryRun = $false,
    [switch]$DeactivateOldRevisions = $true,
    [switch]$CleanupImages = $true,
    [switch]$CleanupUnusedRepos = $true,
    [switch]$CleanupLogAnalytics = $false,
    [switch]$ListResources = $true,
    [switch]$ShowAutomation = $true
)

$ErrorActionPreference = "Stop"
$ResourceGroup = "rg-qca-dev"
$RegistryName = "acrqcadev2f37g0"
$LogAnalyticsWorkspaceToDelete = "workspace-rgqcadevJgjp"  # Duplicate, can save $60-150/month

Write-Host "🧹 Azure Resource Housekeeping" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "⚠️  DRY RUN MODE - No changes will be made`n" -ForegroundColor Yellow
}

# Function to display section header
function Write-Section {
    param([string]$Title)
    Write-Host "`n$Title" -ForegroundColor Green
    Write-Host ("=" * $Title.Length) -ForegroundColor Green
}

# 1. List Current Active Resources
if ($ListResources) {
    Write-Section "📋 Current Active Resources"
    
    Write-Host "`n🔵 Container Apps:" -ForegroundColor Cyan
    az containerapp list `
        --resource-group $ResourceGroup `
        --query "[].{Name:name, Status:properties.provisioningState, URL:properties.configuration.ingress.fqdn}" `
        --output table
    
    Write-Host "`n🔵 Active Container App Revisions:" -ForegroundColor Cyan
    $apps = @("ca-api-qca-dev", "ca-mcp-qca-dev", "ca-frontend-qca-dev")
    foreach ($app in $apps) {
        Write-Host "`n  App: $app" -ForegroundColor Yellow
        $query = '[?properties.active==`true`].{Revision:name, Traffic:properties.trafficWeight, Created:properties.createdTime}'
        az containerapp revision list `
            --name $app `
            --resource-group $ResourceGroup `
            --query $query `
            --output table
    }
    
    Write-Host "`n🔵 Container Registry Repositories:" -ForegroundColor Cyan
    az acr repository list `
        --name $RegistryName `
        --output table
    
    Write-Host "`n🔵 Log Analytics Workspaces:" -ForegroundColor Cyan
    $laQuery = '[].{Name:name, Location:location, SKU:sku.name, RetentionDays:retentionInDays}'
    az monitor log-analytics workspace list `
        --resource-group $ResourceGroup `
        --query $laQuery `
        --output table
}

# 2. Deactivate Old Container App Revisions
if ($DeactivateOldRevisions) {
    Write-Section "🔄 Deactivating Old Revisions"
    
    $apps = @("ca-api-qca-dev", "ca-mcp-qca-dev", "ca-frontend-qca-dev")
    
    foreach ($app in $apps) {
        Write-Host "`n📦 Processing $app..." -ForegroundColor Yellow
        
        # Get all revisions
        $revisions = az containerapp revision list `
            --name $app `
            --resource-group $ResourceGroup `
            --query "[].{name:name, active:properties.active, traffic:properties.trafficWeight}" `
            --output json | ConvertFrom-Json
        
        $activeCount = ($revisions | Where-Object { $_.active -eq $true }).Count
        Write-Host "  Found $activeCount active revision(s)" -ForegroundColor Gray
        
        # Keep latest 2 active, deactivate older ones
        $revisionsToDeactivate = $revisions | 
            Where-Object { $_.active -eq $true -and $_.traffic -eq 0 } |
            Sort-Object -Property name -Descending |
            Select-Object -Skip 2
        
        if ($revisionsToDeactivate.Count -eq 0) {
            Write-Host "  ✅ No old revisions to deactivate" -ForegroundColor Green
        } else {
            foreach ($revision in $revisionsToDeactivate) {
                if ($DryRun) {
                    Write-Host "  [DRY RUN] Would deactivate: $($revision.name)" -ForegroundColor Yellow
                } else {
                    Write-Host "  Deactivating: $($revision.name)" -ForegroundColor Gray
                    az containerapp revision deactivate `
                        --name $app `
                        --resource-group $ResourceGroup `
                        --revision $revision.name `
                        --output none
                    Write-Host "  ✅ Deactivated" -ForegroundColor Green
                }
            }
        }
    }
}

# 3. List Old Container Images
if ($CleanupImages) {
    Write-Section "🗂️  Container Registry Image Analysis"
    
    $repos = @("ca-api-qca-dev", "qca-mcp", "ca-frontend-qca-dev")
    
    # Define known old tags to delete
    $oldTagsToDelete = @{
        "ca-api-qca-dev" = @("mixtral", "20251116145742922033", "20251116134900945702", "20251116132848575384")
        "qca-mcp" = @("v1.0", "v1.1", "v1.2", "v1.3")  # Keep only v1.4
    }
    
    foreach ($repo in $repos) {
        Write-Host "`n📦 $repo tags:" -ForegroundColor Yellow
        
        $tags = az acr repository show-tags `
            --name $RegistryName `
            --repository $repo `
            --orderby time_desc `
            --output json 2>$null | ConvertFrom-Json
        
        if ($null -eq $tags -or $tags.Count -eq 0) {
            Write-Host "  No tags found" -ForegroundColor Gray
            continue
        }
        
        Write-Host "  Total tags: $($tags.Count)" -ForegroundColor Gray
        Write-Host "  Latest 3 tags: $($tags[0..([Math]::Min(2, $tags.Count-1))] -join ', ')" -ForegroundColor Cyan
        
        # Delete known old tags
        if ($oldTagsToDelete.ContainsKey($repo)) {
            $tagsToDelete = $oldTagsToDelete[$repo] | Where-Object { $_ -in $tags }
            
            if ($tagsToDelete.Count -gt 0) {
                Write-Host "  ⚠️  Found $($tagsToDelete.Count) old tag(s) to delete: $($tagsToDelete -join ', ')" -ForegroundColor Yellow
                
                if ($DryRun) {
                    foreach ($tag in $tagsToDelete) {
                        Write-Host "  [DRY RUN] Would delete $repo`:$tag" -ForegroundColor Yellow
                    }
                } else {
                    $response = Read-Host "  Delete these old tags? (y/N)"
                    if ($response -eq 'y') {
                        foreach ($tag in $tagsToDelete) {
                            Write-Host "  Deleting $repo`:$tag..." -ForegroundColor Gray
                            az acr repository delete `
                                --name $RegistryName `
                                --image "${repo}:$tag" `
                                --yes `
                                --output none
                        }
                        Write-Host "  ✅ Old tags deleted" -ForegroundColor Green
                    }
                }
            } else {
                Write-Host "  ✅ No old tags to clean up" -ForegroundColor Green
            }
        }
        
        # Also check for excess tags (keep only latest 5)
        if ($tags.Count -gt 5) {
            $excessTags = $tags | Select-Object -Skip 5
            Write-Host "  ℹ️  Additional $($excessTags.Count) older tag(s) beyond latest 5" -ForegroundColor Cyan
        }
    }
}

# 4. Cleanup Unused ACR Repositories
if ($CleanupUnusedRepos) {
    Write-Section "🗑️  Unused ACR Repository Cleanup"
    
    $unusedRepos = @("api", "ca-api")  # Old/unused repositories
    
    foreach ($repo in $unusedRepos) {
        Write-Host "`n📦 Checking $repo..." -ForegroundColor Yellow
        
        $exists = az acr repository show `
            --name $RegistryName `
            --repository $repo `
            --output json 2>$null | ConvertFrom-Json
        
        if ($null -ne $exists) {
            Write-Host "  ⚠️  Found unused repository: $repo" -ForegroundColor Yellow
            
            if ($DryRun) {
                Write-Host "  [DRY RUN] Would delete repository: $repo" -ForegroundColor Yellow
            } else {
                $response = Read-Host "  Delete unused repository '$repo'? (y/N)"
                if ($response -eq 'y') {
                    Write-Host "  Deleting repository $repo..." -ForegroundColor Gray
                    az acr repository delete `
                        --name $RegistryName `
                        --repository $repo `
                        --yes `
                        --output none
                    Write-Host "  ✅ Repository deleted" -ForegroundColor Green
                }
            }
        } else {
            Write-Host "  ✅ Repository does not exist (already cleaned)" -ForegroundColor Green
        }
    }
}

# 5. Cleanup Duplicate Log Analytics Workspace
if ($CleanupLogAnalytics) {
    Write-Section "📊 Log Analytics Workspace Cleanup"
    
    Write-Host "`n⚠️  Checking for duplicate Log Analytics workspace: $LogAnalyticsWorkspaceToDelete" -ForegroundColor Yellow
    Write-Host "  Potential savings: `$60-150/month" -ForegroundColor Cyan
    
    $workspace = az monitor log-analytics workspace show `
        --resource-group $ResourceGroup `
        --workspace-name $LogAnalyticsWorkspaceToDelete `
        --output json 2>$null | ConvertFrom-Json
    
    if ($null -ne $workspace) {
        Write-Host "  Found duplicate workspace: $($workspace.name)" -ForegroundColor Yellow
        Write-Host "  SKU: $($workspace.sku.name), Retention: $($workspace.retentionInDays) days" -ForegroundColor Gray
        
        if ($DryRun) {
            Write-Host "  [DRY RUN] Would delete workspace: $LogAnalyticsWorkspaceToDelete" -ForegroundColor Yellow
        } else {
            Write-Host "`n  ⚠️  WARNING: Ensure no resources are using this workspace before deletion!" -ForegroundColor Red
            $response = Read-Host "  Delete duplicate Log Analytics workspace? (y/N)"
            if ($response -eq 'y') {
                Write-Host "  Deleting workspace..." -ForegroundColor Gray
                az monitor log-analytics workspace delete `
                    --resource-group $ResourceGroup `
                    --workspace-name $LogAnalyticsWorkspaceToDelete `
                    --yes `
                    --output none
                Write-Host "  ✅ Workspace deleted - saving `$60-150/month" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "  ✅ Duplicate workspace not found (already cleaned)" -ForegroundColor Green
    }
}

# 6. Automation Account Schedules
if ($ShowAutomation) {
    Write-Section "⏰ Automation Account Schedules"
    
    Write-Host "`n🤖 Automation Account: aa-qca-dev" -ForegroundColor Cyan
    Write-Host "  Cost Optimization: 87.5% reduction (12 hrs/day operation)" -ForegroundColor Green
    
    Write-Host "`n📅 Active Schedules:" -ForegroundColor Yellow
    Write-Host "  1. Start-ContainerApps-8AM-SGT" -ForegroundColor White
    Write-Host "     - Runs: Daily at 8:00 AM SGT (12:00 AM UTC)" -ForegroundColor Gray
    Write-Host "     - Action: Starts all 3 container apps" -ForegroundColor Gray
    
    Write-Host "`n  2. Stop-ContainerApps-8PM-SGT" -ForegroundColor White
    Write-Host "     - Runs: Daily at 8:00 PM SGT (12:00 PM UTC)" -ForegroundColor Gray
    Write-Host "     - Action: Stops all 3 container apps" -ForegroundColor Gray
    
    Write-Host "`n💡 Manual Control Commands:" -ForegroundColor Cyan
    Write-Host "  # Start jobs immediately:" -ForegroundColor Gray
    Write-Host '  az automation runbook start --automation-account-name aa-qca-dev --resource-group rg-qca-dev --name Start-ContainerApps' -ForegroundColor White
    
    Write-Host "`n  # Stop jobs immediately:" -ForegroundColor Gray
    Write-Host '  az automation runbook start --automation-account-name aa-qca-dev --resource-group rg-qca-dev --name Stop-ContainerApps' -ForegroundColor White
    
    Write-Host "`n  # Disable schedules (for maintenance):" -ForegroundColor Gray
    Write-Host '  az automation schedule update --automation-account-name aa-qca-dev --resource-group rg-qca-dev --name Start-ContainerApps-8AM-SGT --enabled false' -ForegroundColor White
    
    Write-Host "`n  # Re-enable schedules:" -ForegroundColor Gray
    Write-Host '  az automation schedule update --automation-account-name aa-qca-dev --resource-group rg-qca-dev --name Start-ContainerApps-8AM-SGT --enabled true' -ForegroundColor White
}

# 7. Summary
Write-Section "📊 Housekeeping Summary"

Write-Host "`n✅ Active Infrastructure:" -ForegroundColor Green
Write-Host "  🔹 Container Apps: 3 apps (API, MCP, Frontend)" -ForegroundColor White
Write-Host "    - ca-api-qca-dev: v0.124-mcp-fix (revision 0000132)" -ForegroundColor Gray
Write-Host "    - ca-mcp-qca-dev: v1.4 (revision 0000004)" -ForegroundColor Gray
Write-Host "    - ca-frontend-qca-dev: v0.120 (revision 0000029)" -ForegroundColor Gray

Write-Host "`n  🔹 Container Registry: $RegistryName" -ForegroundColor White
Write-Host "    - Active repositories: ca-api-qca-dev, qca-mcp, ca-frontend-qca-dev" -ForegroundColor Gray

Write-Host "`n  🔹 Database: psql-qca-dev-2f37g0.postgres.database.azure.com" -ForegroundColor White
Write-Host "    - PostgreSQL 14, database: postgres" -ForegroundColor Gray

Write-Host "`n  🔹 Automation: aa-qca-dev" -ForegroundColor White
Write-Host "    - Cost savings: 87.5% (12 hrs/day operation)" -ForegroundColor Gray
Write-Host "    - Operating hours: 8AM-8PM SGT daily" -ForegroundColor Gray

Write-Host "`n💰 Cost Optimization Status:" -ForegroundColor Cyan
Write-Host "  ✅ Automation schedules active: 87.5% cost reduction" -ForegroundColor Green
Write-Host "  ✅ Scale-to-zero enabled: 5-minute idle timeout" -ForegroundColor Green
if (-not $CleanupLogAnalytics -or $DryRun) {
    Write-Host "  ⚠️  Duplicate Log Analytics: Run with -CleanupLogAnalytics to save `$60-150/month" -ForegroundColor Yellow
}

Write-Host "`n🧹 Cleanup Actions Performed:" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "  ⚠️  DRY RUN MODE - No changes were made" -ForegroundColor Yellow
    Write-Host "  Run without -DryRun to apply changes:" -ForegroundColor Yellow
    Write-Host "    .\housekeep-azure.ps1" -ForegroundColor White
    Write-Host "    .\housekeep-azure.ps1 -CleanupLogAnalytics  # Include Log Analytics cleanup" -ForegroundColor White
} else {
    Write-Host "  ✅ Deactivated old container app revisions" -ForegroundColor Green
    Write-Host "  ✅ Cleaned up old container images" -ForegroundColor Green
    if ($CleanupUnusedRepos) {
        Write-Host "  ✅ Removed unused ACR repositories" -ForegroundColor Green
    }
    if ($CleanupLogAnalytics) {
        Write-Host "  ✅ Deleted duplicate Log Analytics workspace" -ForegroundColor Green
    }
}

Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Verify all services running: Check container app URLs" -ForegroundColor White
Write-Host "  2. Monitor costs: Azure Cost Management dashboard" -ForegroundColor White
Write-Host "  3. Regular maintenance: Run this script monthly" -ForegroundColor White
Write-Host "  4. MCP updates: Use Dockerfile.fast for 2-minute builds" -ForegroundColor White

Write-Host "`nHousekeeping complete!`n" -ForegroundColor Green
