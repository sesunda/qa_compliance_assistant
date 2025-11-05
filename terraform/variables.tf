variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "westus2"  # Changed to westus2 - eastus has PostgreSQL quota restrictions
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "qca"
}

variable "admin_email" {
  description = "Administrator email for notifications"
  type        = string
  default     = "senthilkumar@quantiqueanalytica.com"
}

# Database Configuration
variable "db_admin_username" {
  description = "PostgreSQL administrator username"
  type        = string
  default     = "qcaadmin"
  sensitive   = true
}

variable "db_admin_password" {
  description = "PostgreSQL administrator password"
  type        = string
  sensitive   = true
}

variable "db_sku_name" {
  description = "PostgreSQL SKU name for DEV environment"
  type        = string
  default     = "B_Standard_B1ms" # Burstable tier for cost optimization
}

variable "db_storage_mb" {
  description = "PostgreSQL storage size in MB"
  type        = number
  default     = 32768 # 32 GB
}

# Container Apps Configuration
variable "api_cpu" {
  description = "CPU allocation for API container"
  type        = number
  default     = 0.5
}

variable "api_memory" {
  description = "Memory allocation for API container (in Gi)"
  type        = string
  default     = "1Gi"
}

variable "api_min_replicas" {
  description = "Minimum replicas for API container"
  type        = number
  default     = 1
}

variable "api_max_replicas" {
  description = "Maximum replicas for API container"
  type        = number
  default     = 3
}

variable "frontend_cpu" {
  description = "CPU allocation for Frontend container"
  type        = number
  default     = 0.5
}

variable "frontend_memory" {
  description = "Memory allocation for Frontend container (in Gi)"
  type        = string
  default     = "1Gi"
}

variable "mcp_cpu" {
  description = "CPU allocation for MCP Server container"
  type        = number
  default     = 0.25
}

variable "mcp_memory" {
  description = "Memory allocation for MCP Server container (in Gi)"
  type        = string
  default     = "0.5Gi"
}

# LLM Configuration
variable "llm_provider" {
  description = "LLM provider (groq, openai, anthropic)"
  type        = string
  default     = "groq"
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "groq_api_key" {
  description = "Groq API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "anthropic_api_key" {
  description = "Anthropic API key"
  type        = string
  sensitive   = true
  default     = ""
}

# Tags
variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "QA Compliance Assistant"
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}
