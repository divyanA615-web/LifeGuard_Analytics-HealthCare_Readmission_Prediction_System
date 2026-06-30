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

resource "google_kms_key_ring" "main" {
  project  = var.project_id
  name     = "${var.env}-lifeguard-keyring"
  location = var.region
}

resource "google_kms_crypto_key" "phi" {
  project     = var.project_id
  name        = "${var.env}-lifeguard-phi-key"
  key_ring    = google_kms_key_ring.main.id
  purpose     = "ENCRYPT_DECRYPT"
  rotation_period = "7776000s"
  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "SOFTWARE"
  }
}

resource "google_kms_crypto_key" "storage" {
  project     = var.project_id
  name        = "${var.env}-lifeguard-storage-key"
  key_ring    = google_kms_key_ring.main.id
  purpose     = "ENCRYPT_DECRYPT"
  rotation_period = "7776000s"
}

output "cmek_key_resource" {
  value = google_kms_crypto_key.phi.id
}

output "storage_key_resource" {
  value = google_kms_crypto_key.storage.id
}
