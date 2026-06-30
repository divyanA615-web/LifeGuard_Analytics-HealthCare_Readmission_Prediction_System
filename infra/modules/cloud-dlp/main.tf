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

resource "google_data_loss_prevention_inspect_template" "phi_lite" {
  project    = var.project_id
  parent     = "organizations/${var.project_id}"
  location   = var.region
  template_id = "lifeguard-phi-lite"
  inspect_config {
    info_types {
      name = "PERSON_NAME"
    }
    info_types {
      name = "US_SOCIAL_SECURITY_NUMBER"
    }
    info_types {
      name = "DATE_OF_BIRTH"
    }
    info_types {
      name = "PHONE_NUMBER"
    }
    info_types {
      name = "EMAIL_ADDRESS"
    }
    info_types {
      name = "US_MEDICAL_RECORD_NUMBER"
    }
    min_likelihood = "LIKELY"
  }
}

resource "google_data_loss_prevention_deidentify_template" "scrub" {
  project    = var.project_id
  parent     = "organizations/${var.project_id}"
  location   = var.region
  template_id = "lifeguard-deid-scrub"
  deidentify_config {
    info_type_transformations {
      transformations {
        primitive_transformation {
          replace_with_info_type_config {}
        }
      }
    }
  }
}

output "inspect_template" {
  value = google_data_loss_prevention_inspect_template.phi_lite.name
}

output "deid_template" {
  value = google_data_loss_prevention_deidentify_template.scrub.name
}
