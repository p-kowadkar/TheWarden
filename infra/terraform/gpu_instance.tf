# ─────────────────────────────────────────────────────────────────────────────
# T4 GPU Instance Template — Pixel Streaming
#
# This instance is NOT auto-started. It is launched on-demand via the GCP
# Console or gcloud CLI when a Pixel Streaming session is required.
#
# To start:  gcloud compute instances start warden-pixel-streaming --zone us-central1-a
# To stop:   gcloud compute instances stop warden-pixel-streaming --zone us-central1-a
#
# The auto_shutdown.sh script (installed by startup.sh) will stop the instance
# automatically if NetworkIn drops below 1 MB for 10 consecutive minutes.
# ─────────────────────────────────────────────────────────────────────────────

resource "google_compute_instance_template" "pixel_streaming" {
  name_prefix  = "warden-pixel-streaming-"
  machine_type = "n1-standard-4"
  region       = var.region

  disk {
    source_image = "projects/windows-cloud/global/images/family/windows-2022"
    auto_delete  = true
    boot         = true
    disk_size_gb = 100
    disk_type    = "pd-ssd"
  }

  guest_accelerator {
    type  = "nvidia-tesla-t4"
    count = 1
  }

  scheduling {
    on_host_maintenance = "TERMINATE"
    automatic_restart   = false
  }

  network_interface {
    network    = google_compute_network.warden_vpc.id
    subnetwork = google_compute_subnetwork.warden_subnet.id
    access_config {}  # Ephemeral public IP for HTTPS endpoint
  }

  metadata = {
    windows-startup-script-ps1 = file("${path.module}/../scripts/startup.sh")
  }

  tags = ["pixel-streaming", "warden-gpu"]

  lifecycle {
    create_before_destroy = true
  }
}

# Firewall: allow HTTPS and WebSocket traffic to the Pixel Streaming instance
resource "google_compute_firewall" "pixel_streaming_ingress" {
  name    = "warden-pixel-streaming-ingress"
  network = google_compute_network.warden_vpc.id

  allow {
    protocol = "tcp"
    ports    = ["443", "80", "8888"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["pixel-streaming"]
}

# Managed instance group (size=0 — not running until manually started)
resource "google_compute_instance_group_manager" "pixel_streaming" {
  name               = "warden-pixel-streaming-mig"
  base_instance_name = "warden-pixel-streaming"
  zone               = var.zone
  target_size        = 0  # On-demand only — do not auto-start

  version {
    instance_template = google_compute_instance_template.pixel_streaming.id
  }
}
