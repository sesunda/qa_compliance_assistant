# Azure Resource Housekeeping Script - Simplified
# Comprehensive cleanup for QCA Compliance Assistant

param(
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"
$ResourceGroup = "rg-qca-dev"
$RegistryName = "acrqcadev2f37g0"

Write-Host "`n=== Azure Resource Housekeeping ===" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "DRY RUN MODE - No changes will be made`n" -ForegroundColor Yellow
}

# 1. List Current Resources
Write-Host "`n--- Current Active Resources ---" -ForegroundColor Green

Write-Host "`nContainer Apps:" -ForegroundColor Cyan
az containerapp list --resource-group $ResourceGroup --query "[].{Name:name, Status:properties.provisioningState}" --output table

Write-Host "`nContainer Registry Repositories:" -ForegroundColor Cyan
az acr repository list --name $RegistryName --output table

# 2. Deactivate Old Container App Revisions
Write-Host "`n--- Deactivating Old Revisions ---" -ForegroundColor Green

$apps = @("ca-api-qca-dev", "ca-mcp-qca-dev", "ca-frontend-qca-dev")

foreach ($app in $apps) {
    Write-Host "`nProcessing $app..." -ForegroundColor Yellow
    
    $revisions = az containerapp revision list --name $app --resource-group $ResourceGroup --query "[].{name:name, active:properties.active, traffic:properties.trafficWeight}" --output json | ConvertFrom-Json
    
    $activeCount = ($revisions | Where-Object { $_.active -eq $true }).Count
    Write-Host "  Found $activeCount active revision(s)" -ForegroundColor Gray
    
    # Keep latest 2 active, deactivate older ones with no traffic
    $revisionsToDeactivate = $revisions | 
        Where-Object { $_.active -eq $true -and $_.traffic -eq 0 } |
        Sort-Object -Property name -Descending |
        Select-Object -Skip 2
    
    if ($revisionsToDeactivate.Count -eq 0) {
        Write-Host "  No old revisions to deactivate" -ForegroundColor Green
    } else {
        foreach ($revision in $revisionsToDeactivate) {
            if ($DryRun) {
                Write-Host "  [DRY RUN] Would deactivate: $($revision.name)" -ForegroundColor Yellow
            } else {
                Write-Host "  Deactivating: $($revision.name)" -ForegroundColor Gray
                az containerapp revision deactivate --name $app --resource-group $ResourceGroup --revision $revision.name --output none
                Write-Host "  Deactivated" -ForegroundColor Green
            }
        }
    }
}

# 3. Clean Up Old MCP Images
Write-Host "`n--- MCP Image Cleanup ---" -ForegroundColor Green

$mcpTags = az acr repository show-tags --name $RegistryName --repository qca-mcp --orderby time_desc --output json 2>$null | ConvertFrom-Json

if ($mcpTags -and $mcpTags.Count -gt 0) {
    Write-Host "`nMCP Images (Total: $($mcpTags.Count)):" -ForegroundColor Yellow
    Write-Host "  Latest: $($mcpTags[0])" -ForegroundColor Cyan
    
    $oldMcpVersions = @("v1.0", "v1.1", "v1.2", "v1.3")
    $mcpToDelete = $oldMcpVersions | Where-Object { $_ -in $mcpTags }
    
    if ($mcpToDelete.Count -gt 0) {
        Write-Host "  Old versions to delete: $($mcpToDelete -join ', ')" -ForegroundColor Yellow
        
        if ($DryRun) {
            Write-Host "  [DRY RUN] Would delete old MCP versions" -ForegroundColor Yellow
        } else {
            $response = Read-Host "  Delete old MCP versions? (y/N)"
            if ($response -eq 'y') {
                foreach ($tag in $mcpToDelete) {
                    Write-Host "  Deleting qca-mcp:$tag..." -ForegroundColor Gray
                    az acr repository delete --name $RegistryName --image "qca-mcp:$tag" --yes --output none
                }
                Write-Host "  Deleted old MCP versions" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "  No old MCP versions to delete" -ForegroundColor Green
    }
}

# 4. Clean Up Old API Images
Write-Host "`n--- API Image Cleanup ---" -ForegroundColor Green

$apiTags = az acr repository show-tags --name $RegistryName --repository ca-api-qca-dev --orderby time_desc --output json 2>$null | ConvertFrom-Json

if ($apiTags -and $apiTags.Count -gt 0) {
    Write-Host "`nAPI Images (Total: $($apiTags.Count)):" -ForegroundColor Yellow
    Write-Host "  Latest 3: $($apiTags[0..([Math]::Min(2, $apiTags.Count-1))] -join ', ')" -ForegroundColor Cyan
    
    $oldApiTags = @("mixtral", "20251116145742922033", "20251116134900945702", "20251116132848575384")
    $apiToDelete = $oldApiTags | Where-Object { $_ -in $apiTags }
    
    if ($apiToDelete.Count -gt 0) {
        Write-Host "  Old tags to delete: $($apiToDelete -join ', ')" -ForegroundColor Yellow
        
        if ($DryRun) {
            Write-Host "  [DRY RUN] Would delete old API tags" -ForegroundColor Yellow
        } else {
            $response = Read-Host "  Delete old API tags? (y/N)"
            if ($response -eq 'y') {
                foreach ($tag in $apiToDelete) {
                    Write-Host "  Deleting ca-api-qca-dev:$tag..." -ForegroundColor Gray
                    az acr repository delete --name $RegistryName --image "ca-api-qca-dev:$tag" --yes --output none
                }
                Write-Host "  Deleted old API tags" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "  No old API tags to delete" -ForegroundColor Green
    }
}

# 5. Clean Up Unused Repositories
Write-Host "`n--- Unused Repository Cleanup ---" -ForegroundColor Green

$unusedRepos = @("api", "ca-api")

foreach ($repo in $unusedRepos) {
    Write-Host "`nChecking $repo..." -ForegroundColor Yellow
    
    # Check if repo exists by listing all repos
    $allRepos = az acr repository list --name $RegistryName --output json | ConvertFrom-Json
    $exists = $repo -in $allRepos
    
    if ($exists) {
        Write-Host "  Found unused repository: $repo" -ForegroundColor Yellow
        
        if ($DryRun) {
            Write-Host "  [DRY RUN] Would delete repository" -ForegroundColor Yellow
        } else {
            $response = Read-Host "  Delete unused repository '$repo'? (y/N)"
            if ($response -eq 'y') {
                Write-Host "  Deleting repository..." -ForegroundColor Gray
                az acr repository delete --name $RegistryName --repository $repo --yes --output none
                Write-Host "  Deleted repository" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "  Repository does not exist (already cleaned)" -ForegroundColor Green
    }
}

# Summary
Write-Host "`n--- Summary ---" -ForegroundColor Green

Write-Host "`nActive Infrastructure:" -ForegroundColor Cyan
Write-Host "  - Container Apps: ca-api-qca-dev (v0.124-mcp-fix), ca-mcp-qca-dev (v1.4), ca-frontend-qca-dev (v0.120)"
Write-Host "  - Container Registry: $RegistryName"
Write-Host "  - Database: psql-qca-dev-2f37g0.postgres.database.azure.com"
Write-Host "  - Automation: aa-qca-dev (8AM-8PM SGT, 87.5% cost savings)"

Write-Host "`nCost Optimization:" -ForegroundColor Cyan
Write-Host "  - Automation schedules active: 87.5% reduction"
Write-Host "  - Scale-to-zero enabled: 5-minute idle timeout"

if ($DryRun) {
    Write-Host "`nDRY RUN - No changes were made" -ForegroundColor Yellow
    Write-Host "Run without -DryRun to apply changes" -ForegroundColor Yellow
}

Write-Host "`nHousekeeping complete!`n" -ForegroundColor Green
