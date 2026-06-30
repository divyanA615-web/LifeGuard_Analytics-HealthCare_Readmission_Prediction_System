terraform {
  required_version = ">= 1.9.0"
}

module "bootstrap" {
  source     = "./modules/bootstrap"
  project_id = var.project_id
  region     = var.region
  env        = var.env
}

module "network" {
  source          = "./modules/networking"
  project_id      = var.project_id
  region          = var.region
  env             = var.env
  vpc_cidr        = var.vpc_cidr
  pods_cidr       = var.pods_cidr
  services_cidr   = var.services_cidr
}

module "kms" {
  source     = "./modules/cloud-kms"
  project_id = var.project_id
  region     = var.region
  env        = var.env
}

module "storage" {
  source           = "./modules/storage"
  project_id       = var.project_id
  region           = var.region
  env              = var.env
  kms_key_resource = module.kms.cmek_key_resource
}

module "dlp" {
  source     = "./modules/cloud-dlp"
  project_id = var.project_id
  region     = var.region
  env        = var.env
}

module "cloudsql" {
  source            = "./modules/cloud-sql"
  project_id        = var.project_id
  region            = var.region
  env               = var.env
  network_self_link = module.network.vpc_self_link
  kms_key_resource  = module.kms.cmek_key_resource
  db_tier           = var.db_tier
  ha                = var.ha
}

module "cloudrun" {
  source              = "./modules/cloud-run"
  project_id          = var.project_id
  region              = var.region
  env                 = var.env
  api_image           = var.api_image
  frontend_image      = var.frontend_image
  vpc_connector_id    = module.network.vpc_connector_id
  cloudsql_connector  = module.cloudsql.connection_name
  artifact_bucket     = module.storage.bucket_names["models"]
  kms_key_resource    = module.kms.cmek_key_resource
  webhook_slack_url   = var.slack_webhook_url
  budget_alert_emails = var.budget_alert_emails
}

output "project_id" {
  value = var.project_id
}

output "region" {
  value = var.region
}

output "cloudsql_connection" {
  value = module.cloudsql.connection_name
}

output "artifact_bucket" {
  value = module.storage.bucket_names["models"]
}
