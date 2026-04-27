output "cloud_run_url" {
  description = "Public URL of the warden_backend Cloud Run service"
  value       = google_cloud_run_v2_service.warden_backend.uri
}

output "cloud_sql_private_ip" {
  description = "Private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.warden_db.private_ip_address
  sensitive   = true
}

output "vpc_connector_id" {
  description = "VPC Access Connector ID used by Cloud Run"
  value       = google_vpc_access_connector.warden_connector.id
}

output "db_instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.warden_db.name
}
