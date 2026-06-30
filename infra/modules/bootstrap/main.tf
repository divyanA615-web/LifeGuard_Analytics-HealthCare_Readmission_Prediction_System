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

locals {
  api_services = [
    "compute.googleapis.com",
    "sqladmin.googleapis.com",
    "sql-component.googleapis.com",
    "storage.googleapis.com",
    "storage-component.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudkms.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    "cloudbuild.googleapis.com",
    "dns.googleapis.com",
    "servicenetworking.googleapis.com",
    "certificatemanager.googleapis.com",
    "healthcare.googleapis.com",
    "run.googleapis.com",
    "dlp.googleapis.com",
    "pubsub.googleapis.com",
  ]
}

resource "google_project_service" "api" {
  for_each = { for s in local.api_services : s => s }
  project  = var.project_id
  service  = each.value

  disable_on_destroy = false
}
