terraform {
  required_version = ">= 1.9.0"
}

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "env" {
  type = string
}

variable "network_self_link" {
  type = string
}

variable "kms_key_resource" {
  type = string
}

variable "db_tier" {
  type    = string
  default = "db-f1-micro"
}

variable "ha" {
  type    = bool
  default = false
}

data "google_secret_manager_secret_version" "db_password" {
  secret  = "${var.project_id}-db-password"
}

resource "google_sql_database_instance" "main" {
  project          = var.project_id
  name             = "${var.env}-lifeguard-pg"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = var.db_tier
    availability_type = var.ha ? "REGIONAL" : "ZONAL"
    disk_size         = "10"
    disk_type         = "PD-SSD"
    disk_autoresize   = true
    ip_configuration {
      private_network = var.network_self_link
      ipv4_enabled    = false
    }
    backup_configuration {
      enabled            = true
      start_time         = "03:00"
      point_in_time_recovery_enabled = var.ha
    }
    database_flags {
      name  = "cloudsql.enable_pgaudit"
      value = "on"
    }
    encryption_configuration {
      kms_key_name = var.kms_key_resource
    }
    user_labels = {
      project  = "lifeguard"
      env      = var.env
      workload = "readmission"
    }
  }

  deletion_protection = (var.env == "prod")
}

resource "google_sql_database" "main" {
  project = var.project_id
  instance = google_sql_database_instance.main.name
  name     = "lifeguard"
}

resource "google_sql_user" "app" {
  project  = var.project_id
  instance = google_sql_database_instance.main.name
  name     = "lifeguard_app"
  password = data.google_secret_manager_secret_version.db_password.secret_data
}

output "connection_name" {
  value = google_sql_database_instance.main.connection_name
}

output "self_link" {
  value = google_sql_database_instance.main.self_link
}
