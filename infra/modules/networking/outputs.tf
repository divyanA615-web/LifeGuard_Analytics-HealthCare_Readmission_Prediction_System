output "vpc_self_link" {
  value = google_compute_network.main.self_link
}

output "vpc_connector_id" {
  value = google_vpc_access_connector.cloudrun.id
}

output "subnet_self_link" {
  value = google_compute_subnetwork.private.self_link
}
