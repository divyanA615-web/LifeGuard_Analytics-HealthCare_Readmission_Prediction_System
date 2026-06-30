terraform {
  backend "gcs" {
    bucket = "lifeguard-tf-state"
    prefix = "env/prod"
  }
}

provider "google" {
  project = "project-b0677df0-7b67-4302-a4a"
  region  = "asia-south1"
}
