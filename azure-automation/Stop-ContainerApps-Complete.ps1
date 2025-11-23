# Stop Container Apps completely by disabling ingress and deactivating revisions
# This ensures zero replicas and cost during shutdown period (8 PM - 8 AM SGT)

param()

# Connect using managed identity
Connect-AzAccount -Identity

$resourceGroup = "rg-qca-dev"
$apps = @("ca-api-qca-dev", "ca-frontend-qca-dev", "ca-mcp-qca-dev")

foreach ($appName in $apps) {
    Write-Output "Stopping $appName completely..."
    
    try {
        # Step 1: Disable ingress to stop all incoming traffic
        Write-Output "  - Disabling ingress for $appName..."
        az containerapp ingress disable `
            --name $appName `
            --resource-group $resourceGroup `
            --output none
        
        # Step 2: Get all active revisions and deactivate them to force replicas to 0
        Write-Output "  - Deactivating revisions for $appName..."
        $revisions = az containerapp revision list `
            --name $appName `
            --resource-group $resourceGroup `
            --query "[?properties.active].name" `
            --output tsv
        
        foreach ($revision in $revisions) {
            az containerapp revision deactivate `
                --name $appName `
                --resource-group $resourceGroup `
                --revision $revision `
                --output none
        }
        
        Write-Output "✓ $appName stopped successfully (0 replicas)"
    }
    catch {
        Write-Error "Failed to stop $appName : $_"
    }
}

Write-Output "All container apps stopped. Zero replicas = Zero cost during shutdown period."
