# ============================================================================
# LOCALS
# ============================================================================
locals {
  resource_suffix = "${var.project_name}-${var.environment}"
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Location    = var.location
    }
  )
}

# ============================================================================
# RANDOM RESOURCES FOR UNIQUE NAMING
# ============================================================================
resource "random_string" "unique" {
  length  = 6
  special = false
  upper   = false
}

# ============================================================================
# RESOURCE GROUP
# ============================================================================
resource "azurerm_resource_group" "main" {
  name     = "rg-${local.resource_suffix}"
  location = var.location
  tags     = local.common_tags
}

# ============================================================================
# LOG ANALYTICS WORKSPACE
# ============================================================================
resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.common_tags
}

# ============================================================================
# APPLICATION INSIGHTS
# ============================================================================
resource "azurerm_application_insights" "main" {
  name                = "appi-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  tags                = local.common_tags
}

# ============================================================================
# VIRTUAL NETWORK
# ============================================================================
resource "azurerm_virtual_network" "main" {
  name                = "vnet-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  address_space       = ["10.0.0.0/16"]
  tags                = local.common_tags
}

resource "azurerm_subnet" "container_apps" {
  name                 = "snet-container-apps"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.0.0/23"]  # /23 subnet (512 IPs) for Container Apps

  delegation {
    name = "container-apps-delegation"
    service_delegation {
      name    = "Microsoft.App/environments"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

resource "azurerm_subnet" "database" {
  name                 = "snet-database"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.2.0/24"]

  delegation {
    name = "postgres-delegation"
    service_delegation {
      name = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
      ]
    }
  }
}

# ============================================================================
# PRIVATE DNS ZONE FOR POSTGRESQL
# ============================================================================
resource "azurerm_private_dns_zone" "postgres" {
  name                = "privatelink.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.common_tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "postgres-vnet-link"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  virtual_network_id    = azurerm_virtual_network.main.id
  tags                  = local.common_tags
}

# ============================================================================
# POSTGRESQL FLEXIBLE SERVER
# ============================================================================
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "psql-${local.resource_suffix}-${random_string.unique.result}"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "15"
  delegated_subnet_id    = azurerm_subnet.database.id
  private_dns_zone_id    = azurerm_private_dns_zone.postgres.id
  administrator_login    = var.db_admin_username
  administrator_password = var.db_admin_password
  zone                   = "1"
  storage_mb             = var.db_storage_mb
  sku_name               = var.db_sku_name
  backup_retention_days  = 7
  
  # Remove public_network_access_enabled as it conflicts with delegated_subnet_id
  # public_network_access_enabled = false

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]

  tags = local.common_tags
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = "qca_db"
  server_id = azurerm_postgresql_flexible_server.main.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# ============================================================================
# STORAGE ACCOUNT FOR EVIDENCE AND REPORTS
# ============================================================================
resource "azurerm_storage_account" "main" {
  name                     = "st${var.project_name}${var.environment}${random_string.unique.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  min_tls_version          = "TLS1_2"

  blob_properties {
    delete_retention_policy {
      days = 7
    }
    container_delete_retention_policy {
      days = 7
    }
  }

  tags = local.common_tags
}

resource "azurerm_storage_container" "evidence" {
  name                  = "evidence"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "reports" {
  name                  = "reports"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# ============================================================================
# KEY VAULT FOR SECRETS
# ============================================================================
data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  name                       = "kv-${local.resource_suffix}-${random_string.unique.result}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get",
      "List",
      "Set",
      "Delete",
      "Purge",
      "Recover"
    ]
  }

  tags = local.common_tags
}

# Store secrets in Key Vault
resource "azurerm_key_vault_secret" "db_connection_string" {
  name         = "db-connection-string"
  value        = "postgresql://${var.db_admin_username}:${var.db_admin_password}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/qca_db?sslmode=require"
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "storage_connection_string" {
  name         = "storage-connection-string"
  value        = azurerm_storage_account.main.primary_connection_string
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "openai_api_key" {
  count        = var.openai_api_key != "" ? 1 : 0
  name         = "openai-api-key"
  value        = var.openai_api_key
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "groq_api_key" {
  count        = var.groq_api_key != "" ? 1 : 0
  name         = "groq-api-key"
  value        = var.groq_api_key
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "anthropic_api_key" {
  count        = var.anthropic_api_key != "" ? 1 : 0
  name         = "anthropic-api-key"
  value        = var.anthropic_api_key
  key_vault_id = azurerm_key_vault.main.id
}

# ============================================================================
# CONTAINER REGISTRY
# ============================================================================
resource "azurerm_container_registry" "acr" {
  name                = "acr${var.project_name}${var.environment}${random_string.unique.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
  tags                = local.common_tags
}

# ============================================================================
# CONTAINER APPS ENVIRONMENT
# ============================================================================
resource "azurerm_container_app_environment" "main" {
  name                       = "cae-${local.resource_suffix}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  infrastructure_subnet_id   = azurerm_subnet.container_apps.id

  tags = local.common_tags
}

# ============================================================================
# CONTAINER APP - API
# ============================================================================
resource "azurerm_container_app" "api" {
  name                         = "ca-api-${local.resource_suffix}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  registry {
    server               = azurerm_container_registry.acr.login_server
    username             = azurerm_container_registry.acr.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.acr.admin_password
  }

  secret {
    name  = "database-url"
    value = "postgresql://${var.db_admin_username}:${var.db_admin_password}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/qca_db?sslmode=require"
  }

  secret {
    name  = "storage-connection-string"
    value = azurerm_storage_account.main.primary_connection_string
  }

  secret {
    name  = "appinsights-connection-string"
    value = azurerm_application_insights.main.connection_string
  }

  dynamic "secret" {
    for_each = var.openai_api_key != "" ? [1] : []
    content {
      name  = "openai-api-key"
      value = var.openai_api_key
    }
  }

  dynamic "secret" {
    for_each = var.groq_api_key != "" ? [1] : []
    content {
      name  = "groq-api-key"
      value = var.groq_api_key
    }
  }

  dynamic "secret" {
    for_each = var.anthropic_api_key != "" ? [1] : []
    content {
      name  = "anthropic-api-key"
      value = var.anthropic_api_key
    }
  }

  template {
    min_replicas = var.api_min_replicas
    max_replicas = var.api_max_replicas

    container {
      name   = "api"
      image  = "${azurerm_container_registry.acr.login_server}/qca-api:latest"
      cpu    = var.api_cpu
      memory = var.api_memory

      env {
        name        = "DATABASE_URL"
        secret_name = "database-url"
      }

      env {
        name  = "MCP_SERVER_URL"
        value = "https://${azurerm_container_app.mcp_server.latest_revision_fqdn}"
      }

      env {
        name        = "AZURE_STORAGE_CONNECTION_STRING"
        secret_name = "storage-connection-string"
      }

      env {
        name  = "AZURE_STORAGE_CONTAINER_EVIDENCE"
        value = "evidence"
      }

      env {
        name  = "AZURE_STORAGE_CONTAINER_REPORTS"
        value = "reports"
      }

      env {
        name  = "EVIDENCE_STORAGE_BACKEND"
        value = "azure"
      }

      env {
        name  = "LLM_PROVIDER"
        value = var.llm_provider
      }

      dynamic "env" {
        for_each = var.openai_api_key != "" ? [1] : []
        content {
          name        = "OPENAI_API_KEY"
          secret_name = "openai-api-key"
        }
      }

      dynamic "env" {
        for_each = var.groq_api_key != "" ? [1] : []
        content {
          name        = "GROQ_API_KEY"
          secret_name = "groq-api-key"
        }
      }

      dynamic "env" {
        for_each = var.anthropic_api_key != "" ? [1] : []
        content {
          name        = "ANTHROPIC_API_KEY"
          secret_name = "anthropic-api-key"
        }
      }

      env {
        name        = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        secret_name = "appinsights-connection-string"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  tags = local.common_tags
}

# ============================================================================
# CONTAINER APP - MCP SERVER
# ============================================================================
resource "azurerm_container_app" "mcp_server" {
  name                         = "ca-mcp-${local.resource_suffix}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  registry {
    server               = azurerm_container_registry.acr.login_server
    username             = azurerm_container_registry.acr.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.acr.admin_password
  }

  secret {
    name  = "database-url"
    value = "postgresql://${var.db_admin_username}:${var.db_admin_password}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/qca_db?sslmode=require"
  }

  secret {
    name  = "storage-connection-string"
    value = azurerm_storage_account.main.primary_connection_string
  }

  dynamic "secret" {
    for_each = var.groq_api_key != "" ? [1] : []
    content {
      name  = "groq-api-key"
      value = var.groq_api_key
    }
  }

  template {
    min_replicas = 1
    max_replicas = 2

    container {
      name   = "mcp-server"
      image  = "${azurerm_container_registry.acr.login_server}/qca-mcp:latest"
      cpu    = var.mcp_cpu
      memory = var.mcp_memory

      env {
        name        = "DATABASE_URL"
        secret_name = "database-url"
      }

      env {
        name        = "AZURE_STORAGE_CONNECTION_STRING"
        secret_name = "storage-connection-string"
      }

      env {
        name  = "AZURE_STORAGE_CONTAINER_EVIDENCE"
        value = "evidence"
      }

      env {
        name  = "LLM_PROVIDER"
        value = var.llm_provider
      }

      dynamic "env" {
        for_each = var.groq_api_key != "" ? [1] : []
        content {
          name        = "GROQ_API_KEY"
          secret_name = "groq-api-key"
        }
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8001
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  tags = local.common_tags
}

# ============================================================================
# CONTAINER APP - FRONTEND
# ============================================================================
resource "azurerm_container_app" "frontend" {
  name                         = "ca-frontend-${local.resource_suffix}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  registry {
    server               = azurerm_container_registry.acr.login_server
    username             = azurerm_container_registry.acr.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.acr.admin_password
  }

  template {
    min_replicas = 1
    max_replicas = 3

    container {
      name   = "frontend"
      image  = "${azurerm_container_registry.acr.login_server}/qca-frontend:latest"
      cpu    = var.frontend_cpu
      memory = var.frontend_memory

      env {
        name  = "VITE_API_URL"
        value = "https://${azurerm_container_app.api.latest_revision_fqdn}"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 3000
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  tags = local.common_tags
}
