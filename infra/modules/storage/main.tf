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

variable "kms_key_resource" {
  type = string
}

resource "google_storage_bucket" "models" {
  project                     = var.project_id
  name                        = "lifeguard-models-${var.env}"
  location                    = var.region
  force_destroy               = var.env != "prod"
  uniform_bucket_level_access = true
  encryption {
    default_kms_key_name = var.kms_key_resource
  }
  versioning {
    enabled = true
  }
  lifecycle_rule {
    action {
      type = "SetStorageClass"
      storage_class = "COLDLINE"
    }
    condition {
      age = 30
    }
  }
}

resource "google_storage_bucket" "audit" {
  project                     = var.project_id
  name                        = "lifeguard-audit-${var.env}"
  location                    = var.region
  force_destroy               = var.env != "prod"
  uniform_bucket_level_access = true
  encryption {
    default_kms_key_name = var.kms_key_resource
  }
  versioning {
    enabled = true
  }
}

resource "google_storage_bucket" "frontend" {
  project                     = var.project_id
  name                        = "lifeguard-frontend-${var.env}"
  location                    = var.region
  uniform_bucket_level_access = true
  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }
}

output "bucket_names" {
  value = {
    models   = google_storage_bucket.models.name
    audit    = google_storage_bucket.audit.name
    frontend = google_storage_bucket.frontend.name
  }
}
