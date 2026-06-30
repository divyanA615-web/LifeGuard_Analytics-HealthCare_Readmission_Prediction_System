variable "project_id" {
  type    = string
  default = "project-b0677df0-7b67-4302-a4a"
}

variable "region" {
  type    = string
  default = "asia-south1"
}

variable "env" {
  type    = string
  default = "prod"
}

variable "vpc_cidr" {
  type    = string
  default = "10.110.0.0/16"
}

variable "pods_cidr" {
  type    = string
  default = "10.120.0.0/16"
}

variable "services_cidr" {
  type    = string
  default = "10.130.0.0/16"
}

variable "db_tier" {
  type    = string
  default = "db-custom-2-8192"
}

variable "ha" {
  type    = bool
  default = true
}

variable "api_image" {
  type    = string
  default = "gcr.io/cloud-build-images/lifeguard-readmission-api:prod"
}

variable "frontend_image" {
  type    = string
  default = "gcr.io/cloud-build-images/lifeguard-readmission-frontend:prod"
}

variable "slack_webhook_url" {
  type      = string
  default   = "https://hooks.slack.com/services/replace-me"
  sensitive = true
}

variable "budget_alert_emails" {
  type    = list(string)
  default = []
}
