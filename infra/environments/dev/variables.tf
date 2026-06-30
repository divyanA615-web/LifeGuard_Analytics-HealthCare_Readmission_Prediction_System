variable "project_id" {
  description = "GCP project id"
  type        = string
  default     = "project-b0677df0-7b67-4302-a4a"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "asia-south1"
}

variable "env" {
  description = "Environment shortcode (dev|staging|prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.10.0.0/16"
}

variable "pods_cidr" {
  type        = string
  default     = "10.20.0.0/16"
}

variable "services_cidr" {
  type        = string
  default     = "10.30.0.0/16"
}

variable "db_tier" {
  type        = string
  default     = "db-f1-micro"
}

variable "ha" {
  type        = bool
  default     = false
}

variable "api_image" {
  type        = string
  default     = "gcr.io/cloud-build-images/lifeguard-readmission-api:latest"
}

variable "frontend_image" {
  type        = string
  default     = "gcr.io/cloud-build-images/lifeguard-readmission-frontend:latest"
}

variable "slack_webhook_url" {
  type        = string
  default     = "https://hooks.slack.com/services/replace-me"
  sensitive   = true
}

variable "budget_alert_emails" {
  type        = list(string)
  default     = []
}
