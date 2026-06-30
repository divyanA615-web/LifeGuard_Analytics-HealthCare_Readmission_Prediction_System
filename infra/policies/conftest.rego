package terraform.security

# Cloud SQL private IP enforcement
deny[msg] {
  resource := input.resource_changes[_]
  resource.address == "google_sql_database_instance.main"
  resource.change.after.settings[0].ip_configuration[0].ipv4_enabled == true
  msg := sprintf("Cloud SQL instance %s exposes a public IPv4 address", [resource.address])
}

# PHI encryption enforcement
deny[msg] {
  resource := input.resource_changes[_]
  resource.address == "google_sql_database_instance.main"
  resource.change.after.settings[0].encryption_configuration[0].kms_key_name == ""
  msg := sprintf("Cloud SQL instance %s uses Google-managed encryption (no CMEK)", [resource.address])
}

# Cloud Storage CMEK enforcement
deny[msg] {
  resource := input.resource_changes[_]
  startswith(resource.address, "google_storage_bucket.")
  not resource.change.after.encryption[_]
  msg := sprintf("Bucket %s uses default encryption (no CMEK)", [resource.address])
}

# HTTPS-only Cloud Run ingress
deny[msg] {
  resource := input.resource_changes[_]
  resource.address == "google_cloud_run_service.api"
  resource.change.after.metadata[0].annotations["run.googleapis.com/restrictions"] != "internal-only"
  msg := "Cloud Run services must be internal-only"
}
