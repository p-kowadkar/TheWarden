variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone for Compute Engine instances"
  type        = string
  default     = "us-central1-a"
}

variable "db_password" {
  description = "PostgreSQL password for the warden user"
  type        = string
  sensitive   = true
}

variable "budget_alert_email" {
  description = "Email address to receive budget alert notifications"
  type        = string
}

variable "cloud_run_image" {
  description = "Full container image URI for the warden_backend Cloud Run service"
  type        = string
  default     = "gcr.io/PROJECT_ID/warden-backend:latest"
}
