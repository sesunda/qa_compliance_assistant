# Terraform Backend Configuration
# Uncomment and configure this after creating the storage account for state management

# terraform {
#   backend "azurerm" {
#     resource_group_name  = "terraform-state-rg"
#     storage_account_name = "tfstateqcadev"
#     container_name       = "tfstate"
#     key                  = "dev.terraform.tfstate"
#   }
# }
