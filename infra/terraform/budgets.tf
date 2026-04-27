# ─────────────────────────────────────────────────────────────────────────────
# Budget Alerts
#
# Three email notification thresholds: $50, $150, $250.
# Hard stop scaffold at $280: a Pub/Sub topic is created and a budget alert
# publishes to it. The developer connects a Cloud Function to this topic that
# disables billing on the project (requires billing admin IAM role).
#
# NOTE: google_billing_budget requires the billing account ID.
# Set it via: export TF_VAR_billing_account_id=YOUR_BILLING_ACCOUNT_ID
# ─────────────────────────────────────────────────────────────────────────────

variable "billing_account_id" {
  description = "GCP billing account ID (format: XXXXXX-XXXXXX-XXXXXX)"
  type        = string
}

# Pub/Sub topic for the $280 hard-stop trigger
resource "google_pubsub_topic" "budget_hard_stop" {
  name    = "warden-budget-hard-stop"
  project = var.project_id
}

resource "google_billing_budget" "warden_budget" {
  billing_account = var.billing_account_id
  display_name    = "Warden Monthly Budget"

  budget_filter {
    projects = ["projects/${var.project_id}"]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = "300"  # Ceiling above the $280 hard stop
    }
  }

  # Alert at $50 (forecast)
  threshold_rules {
    threshold_percent = 0.167  # ~$50 of $300
    spend_basis       = "FORECASTED_SPEND"
  }

  # Alert at $150 (actual)
  threshold_rules {
    threshold_percent = 0.5    # $150 of $300
    spend_basis       = "CURRENT_SPEND"
  }

  # Alert at $250 (actual)
  threshold_rules {
    threshold_percent = 0.833  # ~$250 of $300
    spend_basis       = "CURRENT_SPEND"
  }

  # Hard stop scaffold at $280 — publishes to Pub/Sub
  # Connect a Cloud Function to this topic to disable billing automatically.
  threshold_rules {
    threshold_percent = 0.933  # ~$280 of $300
    spend_basis       = "CURRENT_SPEND"
  }

  all_updates_rule {
    pubsub_topic                     = google_pubsub_topic.budget_hard_stop.id
    schema_version                   = "1.0"
    monitoring_notification_channels = [google_monitoring_notification_channel.budget_email.name]
    disable_default_iam_recipients   = false
  }
}

# Email notification channel for all budget alerts
resource "google_monitoring_notification_channel" "budget_email" {
  display_name = "Warden Budget Alert Email"
  type         = "email"
  project      = var.project_id

  labels = {
    email_address = var.budget_alert_email
  }
}
