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

variable "vpc_cidr" {
  type    = string
  default = "10.10.0.0/16"
}

variable "pods_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "services_cidr" {
  type    = string
  default = "10.30.0.0/16"
}

resource "google_compute_network" "main" {
  project                 = var.project_id
  name                    = "${var.env}-lifeguard-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "private" {
  project                     = var.project_id
  name                        = "${var.env}-lifeguard-private"
  region                      = var.region
  network                     = google_compute_network.main.name
  ip_cidr_range               = var.vpc_cidr
  private_ip_google_access    = true
  private_ipv6_google_access  = false
  purpose                     = "PRIVATE"
}

resource "google_compute_router" "nat" {
  project  = var.project_id
  name     = "${var.env}-lifeguard-router"
  region   = var.region
  network  = google_compute_network.main.name
}

resource "google_compute_router_nat" "main" {
  project                            = var.project_id
  name                               = "${var.env}-lifeguard-nat"
  router                             = google_compute_router.nat.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  min_ports_per_vm                   = 64
  log_config { filter = "VPC_TUNNEL" enabled = false }
}

resource "google_vpc_access_connector" "cloudrun" {
  provider      = google
  project       = var.project_id
  name          = "${var.env}-lifeguard-conn"
  region        = var.region
  ip_cidr_range = "10.40.0.0/28"

  depends_on = [google_project_service.api_access]
}

data "google_project" "current" {
  project_id = var.project_id
}
