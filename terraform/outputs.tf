output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "container_registry_login_server" {
  description = "Container Registry login server"
  value       = azurerm_container_registry.acr.login_server
}

output "container_registry_name" {
  description = "Container Registry name"
  value       = azurerm_container_registry.acr.name
}

output "api_fqdn" {
  description = "API Container App FQDN"
  value       = azurerm_container_app.api.latest_revision_fqdn
}

output "frontend_fqdn" {
  description = "Frontend Container App FQDN"
  value       = azurerm_container_app.frontend.latest_revision_fqdn
}

output "mcp_server_fqdn" {
  description = "MCP Server Container App FQDN"
  value       = azurerm_container_app.mcp_server.latest_revision_fqdn
}

output "postgresql_fqdn" {
  description = "PostgreSQL server FQDN"
  value       = azurerm_postgresql_flexible_server.main.fqdn
}

output "storage_account_name" {
  description = "Storage account name"
  value       = azurerm_storage_account.main.name
}

output "key_vault_name" {
  description = "Key Vault name"
  value       = azurerm_key_vault.main.name
}

output "application_insights_connection_string" {
  description = "Application Insights connection string"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "application_insights_instrumentation_key" {
  description = "Application Insights instrumentation key"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "deployment_instructions" {
  description = "Next steps for deployment"
  value = <<-EOT
  
  ✅ Infrastructure deployed successfully!
  
  Next steps:
  1. Push Docker images to ACR:
     az acr login --name ${azurerm_container_registry.acr.name}
     
  2. Build and push images:
     docker build -t ${azurerm_container_registry.acr.login_server}/qca-api:latest ./api
     docker build -t ${azurerm_container_registry.acr.login_server}/qca-frontend:latest ./frontend
     docker build -t ${azurerm_container_registry.acr.login_server}/qca-mcp:latest ./mcp_server
     
     docker push ${azurerm_container_registry.acr.login_server}/qca-api:latest
     docker push ${azurerm_container_registry.acr.login_server}/qca-frontend:latest
     docker push ${azurerm_container_registry.acr.login_server}/qca-mcp:latest
  
  3. Access your applications:
     - API: https://${azurerm_container_app.api.latest_revision_fqdn}
     - Frontend: https://${azurerm_container_app.frontend.latest_revision_fqdn}
     - MCP Server: https://${azurerm_container_app.mcp_server.latest_revision_fqdn}
  
  4. Configure GitHub Actions secrets (see AZURE_DEPLOYMENT.md)
  EOT
}
