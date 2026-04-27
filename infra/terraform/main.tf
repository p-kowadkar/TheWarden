terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ─────────────────────────────────────────────────────────────────────────────
# Enable required APIs
# ─────────────────────────────────────────────────────────────────────────────
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "compute.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com",
    "monitoring.googleapis.com",
    "billingbudgets.googleapis.com",
    "vpcaccess.googleapis.com",
    "servicenetworking.googleapis.com",
    "aiplatform.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

# ─────────────────────────────────────────────────────────────────────────────
# VPC
# ─────────────────────────────────────────────────────────────────────────────
resource "google_compute_network" "warden_vpc" {
  name                    = "warden-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis]
}

resource "google_compute_subnetwork" "warden_subnet" {
  name          = "warden-subnet"
  ip_cidr_range = "10.10.0.0/24"
  region        = var.region
  network       = google_compute_network.warden_vpc.id
}

# Private services access for Cloud SQL
resource "google_compute_global_address" "private_ip_range" {
  name          = "warden-private-ip-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.warden_vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.warden_vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
  depends_on              = [google_project_service.apis]
}

# VPC Access Connector for Cloud Run → Cloud SQL private IP
resource "google_vpc_access_connector" "warden_connector" {
  name          = "warden-connector"
  region        = var.region
  subnet {
    name = google_compute_subnetwork.warden_subnet.name
  }
  min_instances = 2
  max_instances = 3
}

# ─────────────────────────────────────────────────────────────────────────────
# Cloud SQL — PostgreSQL 15, db-f1-micro (cheapest)
# ─────────────────────────────────────────────────────────────────────────────
resource "google_sql_database_instance" "warden_db" {
  name             = "warden-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = "db-f1-micro"
    availability_type = "ZONAL"
    disk_size         = 10
    disk_type         = "PD_SSD"

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.warden_vpc.id
    }

    backup_configuration {
      enabled = true
    }
  }

  deletion_protection = false
  depends_on          = [google_service_networking_connection.private_vpc_connection]
}

resource "google_sql_database" "warden" {
  name     = "warden_db"
  instance = google_sql_database_instance.warden_db.name
}

resource "google_sql_user" "warden_user" {
  name     = "warden"
  instance = google_sql_database_instance.warden_db.name
  password = var.db_password
}

# ─────────────────────────────────────────────────────────────────────────────
# Cloud Run — warden_backend
# Scale to zero when idle; min-instances=0
# ─────────────────────────────────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "warden_backend" {
  name     = "warden-backend"
  location = var.region

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    vpc_access {
      connector = google_vpc_access_connector.warden_connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = var.cloud_run_image

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_LOCATION"
        value = var.region
      }
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_url.secret_id
            version = "latest"
          }
        }
      }

      ports {
        container_port = 8080
      }
    }
  }

  depends_on = [google_project_service.apis]
}

# Allow unauthenticated invocations (WebSocket from Unreal client)
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.warden_backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ─────────────────────────────────────────────────────────────────────────────
# Secret Manager — DATABASE_URL
# ─────────────────────────────────────────────────────────────────────────────
resource "google_secret_manager_secret" "db_url" {
  secret_id = "warden-db-url"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}
