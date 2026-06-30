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

variable "api_image" {
  type = string
}

variable "frontend_image" {
  type = string
}

variable "vpc_connector_id" {
  type = string
}

variable "cloudsql_connector" {
  type = string
}

variable "artifact_bucket" {
  type = string
}

variable "kms_key_resource" {
  type = string
}

variable "webhook_slack_url" {
  type      = string
  sensitive = true
  default   = "https://hooks.slack.com/services/replace-me"
}

variable "budget_alert_emails" {
  type    = list(string)
  default = []
}

resource "google_service_account" "api" {
  project      = var.project_id
  account_id   = "lifeguard-api-${var.env}"
  display_name = "LifeGuard API"
}

resource "google_project_iam_member" "api_kms" {
  project = var.project_id
  role    = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_secret" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_cloud_run_service" "api" {
  project  = var.project_id
  name     = "${var.env}-lifeguard-api"
  location = var.region
  template {
    spec {
      service_account_name = google_service_account.api.email
      containers {
        image = var.api_image
        resources {
          limits = { cpu = "1", memory = "512Mi" }
        }
        env {
          name  = "ENVIRONMENT"
          value = var.env
        }
        env {
          name  = "PHI_ENCRYPTION_KEY"
          value = var.kms_key_resource
        }
        env {
          name  = "DB_SECRET_NAME"
          value = "${var.project_id}-db-uri"
        }
        env {
          name  = "MODEL_BUCKET"
          value = var.artifact_bucket
        }
      }
    }
    metadata {
      annotations = {
        "run.googleapis.com/max-scale"       = "5"
        "run.googleapis.com/min-scale"       = var.env == "prod" ? "1" : "0"
        "run.googleapis.com/vpc-access-connector" = var.vpc_connector_id
        "run.googleapis.com/network-interfaces" : jsonencode([] )
      }
    }
  }
  traffic {
    percent = 100
    latest_revision = true
  }
  autogenerate_revision_name = true
}

resource "google_cloud_run_service" "frontend" {
  project  = var.project_id
  name     = "${var.env}-lifeguard-frontend"
  location = var.region
  template {
    spec {
      containers {
        image = var.frontend_image
        env {
          name  = "API_BACKEND"
          value = google_cloud_run_service.api.statuses[0].url ?? ""
        }
      }
    }
    metadata {
      annotations = {
        "run.googleapis.com/max-scale" = "3"
        "run.googleapis.com/min-scale" = "0"
      }
    }
  }
  traffic {
    percent = 100
    latest_revision = true
  }
}

output "api_url" {
  value = google_cloud_run_service.api.statuses[0].url
}

output "frontend_url" {
  value = google_cloud_run_service.frontend.statuses[0].url
}

output "api_service_account" {
  value = google_service_account.api.email
}
