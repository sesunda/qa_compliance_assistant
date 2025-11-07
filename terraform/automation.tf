# ============================================================================
# AZURE AUTOMATION ACCOUNT FOR SCHEDULED START/STOP
# ============================================================================

resource "azurerm_automation_account" "main" {
  name                = "aa-qca-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku_name            = "Basic"

  identity {
    type = "SystemAssigned"
  }

  tags = local.common_tags
}

# Grant Automation Account permissions to manage Container Apps
resource "azurerm_role_assignment" "automation_contributor" {
  scope                = azurerm_resource_group.main.id
  role_definition_name = "Contributor"
  principal_id         = azurerm_automation_account.main.identity[0].principal_id
}

# ============================================================================
# RUNBOOK - STOP CONTAINER APPS (Scale to 0)
# ============================================================================

resource "azurerm_automation_runbook" "stop_containers" {
  name                    = "Stop-ContainerApps"
  location                = azurerm_resource_group.main.location
  resource_group_name     = azurerm_resource_group.main.name
  automation_account_name = azurerm_automation_account.main.name
  log_verbose             = "true"
  log_progress            = "true"
  runbook_type            = "PowerShell"

  content = <<-POWERSHELL
    param(
        [string]$ResourceGroupName,
        [string]$ApiAppName,
        [string]$FrontendAppName,
        [string]$McpAppName
    )

    # Connect using Managed Identity
    Connect-AzAccount -Identity

    Write-Output "Scaling down Container Apps to 0 replicas..."

    # Scale API to 0
    az containerapp update `
      --name $ApiAppName `
      --resource-group $ResourceGroupName `
      --min-replicas 0 `
      --max-replicas 0

    Write-Output "API scaled to 0"

    # Scale Frontend to 0
    az containerapp update `
      --name $FrontendAppName `
      --resource-group $ResourceGroupName `
      --min-replicas 0 `
      --max-replicas 0

    Write-Output "Frontend scaled to 0"

    # Scale MCP to 0
    az containerapp update `
      --name $McpAppName `
      --resource-group $ResourceGroupName `
      --min-replicas 0 `
      --max-replicas 0

    Write-Output "MCP Server scaled to 0"
    Write-Output "All Container Apps stopped successfully"
  POWERSHELL

  tags = local.common_tags
}

# ============================================================================
# RUNBOOK - START CONTAINER APPS (Restore min replicas)
# ============================================================================

resource "azurerm_automation_runbook" "start_containers" {
  name                    = "Start-ContainerApps"
  location                = azurerm_resource_group.main.location
  resource_group_name     = azurerm_resource_group.main.name
  automation_account_name = azurerm_automation_account.main.name
  log_verbose             = "true"
  log_progress            = "true"
  runbook_type            = "PowerShell"

  content = <<-POWERSHELL
    param(
        [string]$ResourceGroupName,
        [string]$ApiAppName,
        [string]$FrontendAppName,
        [string]$McpAppName
    )

    # Connect using Managed Identity
    Connect-AzAccount -Identity

    Write-Output "Starting Container Apps..."

    # Start API (restore to scale-to-zero settings)
    az containerapp update `
      --name $ApiAppName `
      --resource-group $ResourceGroupName `
      --min-replicas 0 `
      --max-replicas 3

    Write-Output "API started (scale-to-zero enabled)"

    # Start Frontend (restore to scale-to-zero settings)
    az containerapp update `
      --name $FrontendAppName `
      --resource-group $ResourceGroupName `
      --min-replicas 0 `
      --max-replicas 3

    Write-Output "Frontend started (scale-to-zero enabled)"

    # Start MCP (restore to scale-to-zero settings)
    az containerapp update `
      --name $McpAppName `
      --resource-group $ResourceGroupName `
      --min-replicas 0 `
      --max-replicas 3

    Write-Output "MCP Server started (scale-to-zero enabled)"
    Write-Output "All Container Apps started successfully"
  POWERSHELL

  tags = local.common_tags
}

# ============================================================================
# SCHEDULES - STOP at 8 PM SGT, START at 8 AM SGT
# ============================================================================

# Schedule: STOP at 8 PM SGT (12 PM UTC)
resource "azurerm_automation_schedule" "stop_schedule" {
  name                    = "Stop-ContainerApps-8PM-SGT"
  resource_group_name     = azurerm_resource_group.main.name
  automation_account_name = azurerm_automation_account.main.name
  frequency               = "Day"
  interval                = 1
  timezone                = "Singapore Standard Time"
  start_time              = formatdate("YYYY-MM-DD'T'20:00:00+08:00", timeadd(timestamp(), "24h"))
  description             = "Stop all Container Apps at 8 PM SGT to save costs"
}

# Schedule: START at 8 AM SGT (12 AM UTC)
resource "azurerm_automation_schedule" "start_schedule" {
  name                    = "Start-ContainerApps-8AM-SGT"
  resource_group_name     = azurerm_resource_group.main.name
  automation_account_name = azurerm_automation_account.main.name
  frequency               = "Day"
  interval                = 1
  timezone                = "Singapore Standard Time"
  start_time              = formatdate("YYYY-MM-DD'T'08:00:00+08:00", timeadd(timestamp(), "24h"))
  description             = "Start all Container Apps at 8 AM SGT"
}

# ============================================================================
# JOB SCHEDULES - Link Runbooks to Schedules
# ============================================================================

resource "azurerm_automation_job_schedule" "stop_job" {
  resource_group_name     = azurerm_resource_group.main.name
  automation_account_name = azurerm_automation_account.main.name
  runbook_name            = azurerm_automation_runbook.stop_containers.name
  schedule_name           = azurerm_automation_schedule.stop_schedule.name

  parameters = {
    ResourceGroupName = azurerm_resource_group.main.name
    ApiAppName        = azurerm_container_app.api.name
    FrontendAppName   = azurerm_container_app.frontend.name
    McpAppName        = azurerm_container_app.mcp_server.name
  }
}

resource "azurerm_automation_job_schedule" "start_job" {
  resource_group_name     = azurerm_resource_group.main.name
  automation_account_name = azurerm_automation_account.main.name
  runbook_name            = azurerm_automation_runbook.start_containers.name
  schedule_name           = azurerm_automation_schedule.start_schedule.name

  parameters = {
    ResourceGroupName = azurerm_resource_group.main.name
    ApiAppName        = azurerm_container_app.api.name
    FrontendAppName   = azurerm_container_app.frontend.name
    McpAppName        = azurerm_container_app.mcp_server.name
  }
}
