<#
.SYNOPSIS
    Stop all container apps in the QCA DEV environment
    
.DESCRIPTION
    This runbook stops all three container apps (API, Frontend, MCP) 
    by setting their minimum and maximum replicas to 0.
    Scheduled to run daily at 8 PM SGT.
    
.NOTES
    Author: QCA DevOps
    Last Modified: 2025-11-22
    Automation Account: aa-qca-dev
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "rg-qca-dev"
)

Write-Output "========================================="
Write-Output "Stopping Container Apps"
Write-Output "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') UTC"
Write-Output "========================================="

# Authenticate using Managed Identity
Write-Output "`nAuthenticating with Managed Identity..."
try {
    Connect-AzAccount -Identity -ErrorAction Stop | Out-Null
    Write-Output "Authentication successful"
} catch {
    Write-Error "Failed to authenticate: $_"
    exit 1
}

# Define container apps
$apps = @("ca-api-qca-dev", "ca-frontend-qca-dev", "ca-mcp-qca-dev")

Write-Output "`nStopping $($apps.Count) container apps..."

foreach ($appName in $apps) {
    Write-Output "`nProcessing: $appName"
    
    $output = az containerapp update `
        --name $appName `
        --resource-group $ResourceGroup `
        --min-replicas 0 `
        --max-replicas 0 `
        2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Output "  Stopped: $appName"
    } else {
        Write-Warning "  Failed to stop: $appName"
        Write-Output "  Error: $output"
    }
}

Write-Output "`n========================================="
Write-Output "Container apps stop completed"
Write-Output "Cost savings: ~`$0.05/hour"
Write-Output "========================================="
