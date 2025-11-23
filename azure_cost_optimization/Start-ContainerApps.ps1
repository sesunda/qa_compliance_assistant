<#
.SYNOPSIS
    Start all container apps in the QCA DEV environment
    
.DESCRIPTION
    This runbook starts all three container apps (API, Frontend, MCP) 
    by updating their minimum replicas to 1. Scheduled to run daily at 8 AM SGT.
    
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
Write-Output "Starting Container Apps"
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

# Define container apps with scaling config
$apps = @(
    @{Name="ca-api-qca-dev"; Min=1; Max=3},
    @{Name="ca-frontend-qca-dev"; Min=1; Max=3},
    @{Name="ca-mcp-qca-dev"; Min=1; Max=10}
)

Write-Output "`nStarting $($apps.Count) container apps..."

foreach ($app in $apps) {
    Write-Output "`nProcessing: $($app.Name)"
    
    $output = az containerapp update `
        --name $app.Name `
        --resource-group $ResourceGroup `
        --min-replicas $app.Min `
        --max-replicas $app.Max `
        2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Output "  Started: $($app.Name)"
    } else {
        Write-Warning "  Failed to start: $($app.Name)"
        Write-Output "  Error: $output"
    }
}

Write-Output "`n========================================="
Write-Output "Container apps start completed"
Write-Output "========================================="
