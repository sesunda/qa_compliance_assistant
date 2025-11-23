# Start Container Apps by re-enabling ingress
# This creates a new revision and restores apps to operational state (8 AM SGT)

param()

# Connect using managed identity
Connect-AzAccount -Identity

$resourceGroup = "rg-qca-dev"

# Define apps with their ingress configurations
$apps = @(
    @{name="ca-api-qca-dev"; port=8000},
    @{name="ca-frontend-qca-dev"; port=3000},
    @{name="ca-mcp-qca-dev"; port=8001}
)

foreach ($app in $apps) {
    Write-Output "Starting $($app.name)..."
    
    try {
        # Re-enable ingress which will create a new active revision
        Write-Output "  - Enabling ingress for $($app.name)..."
        az containerapp ingress enable `
            --name $app.name `
            --resource-group $resourceGroup `
            --type external `
            --target-port $app.port `
            --transport auto `
            --allow-insecure `
            --output none
        
        Write-Output "✓ $($app.name) started successfully (ready for traffic)"
    }
    catch {
        Write-Error "Failed to start $($app.name) : $_"
    }
}

Write-Output "All container apps started and ready for traffic."
