provider "google" {
  project = "project-b0677df0-7b67-4302-a4a"
  region  = "asia-south1"
}

terraform {
  required_version = ">= 1.9.0"
}

module "bootstrap" {
  source     = "./modules/bootstrap"
  project_id = var.project_id
  region     = var.region
  env        = var.env
}

resource "google_storage_bucket" "tf_state" {
  project                     = "project-b0677df0-7b67-4302-a4a"
  name                        = "lifeguard-tf-state"
  location                    = "ASIA-SOUTH1"
  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
}

variable "project_id" {
  description = "The GCP project id"
  type        = string
  default     = "project-b0677df0-7b67-4302-a4a"
}

variable "region" {
  description = "Primary region"
  type        = string
  default     = "asia-south1"
}

variable "env" {
  description = "Bootstrap suffix (deploys APIs once per environment)"
  type        = string
  default     = "dev"
}

output "state_bucket" {
  value = google_storage_bucket.tf_state.name
}
