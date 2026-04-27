"""
idle_monitor/main.py

Cloud Function: monitors the T4 GPU instance's NetworkIn metric via the
Cloud Monitoring API. If the instance has been idle (NetworkIn < 1 MB/min)
for 10 consecutive minutes, it issues a stop command.

Deploy command:
    gcloud functions deploy warden-idle-monitor \
      --gen2 \
      --runtime python311 \
      --region us-central1 \
      --source infra/cloud_functions/idle_monitor \
      --entry-point check_idle \
      --trigger-http \
      --no-allow-unauthenticated \
      --set-env-vars GCP_PROJECT_ID=YOUR_PROJECT,INSTANCE_NAME=warden-pixel-streaming,INSTANCE_ZONE=us-central1-a

Schedule via Cloud Scheduler (every minute):
    gcloud scheduler jobs create http warden-idle-monitor-scheduler \
      --schedule "* * * * *" \
      --uri "https://REGION-PROJECT_ID.cloudfunctions.net/warden-idle-monitor" \
      --oidc-service-account-email SA@PROJECT.iam.gserviceaccount.com \
      --location us-central1
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

import functions_framework
import googleapiclient.discovery
from google.cloud import compute_v1, monitoring_v3

logger = logging.getLogger(__name__)

PROJECT_ID    = os.environ["GCP_PROJECT_ID"]
INSTANCE_NAME = os.environ.get("INSTANCE_NAME", "warden-pixel-streaming")
INSTANCE_ZONE = os.environ.get("INSTANCE_ZONE", "us-central1-a")

IDLE_THRESHOLD_BYTES = 1 * 1024 * 1024   # 1 MB
IDLE_WINDOW_MINUTES  = 10


@functions_framework.http
def check_idle(request):
    """
    HTTP-triggered Cloud Function entry point.
    Returns a plain-text status string for Cloud Scheduler logging.
    """
    try:
        result = _check_and_maybe_stop()
        return result, 200
    except Exception as exc:
        logger.exception("idle_monitor error")
        return f"ERROR: {exc}", 500


def _check_and_maybe_stop() -> str:
    compute = compute_v1.InstancesClient()

    # ── 1. Is the instance running? ───────────────────────────────────────────
    instance = compute.get(
        project=PROJECT_ID,
        zone=INSTANCE_ZONE,
        instance=INSTANCE_NAME,
    )
    if instance.status != "RUNNING":
        return f"Instance {INSTANCE_NAME} is {instance.status} — nothing to do"

    # ── 2. Query NetworkIn over the last IDLE_WINDOW_MINUTES ─────────────────
    monitoring = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{PROJECT_ID}"

    now = datetime.now(tz=timezone.utc)
    window_start = now - timedelta(minutes=IDLE_WINDOW_MINUTES)

    interval = monitoring_v3.TimeInterval(
        end_time={"seconds": int(now.timestamp())},
        start_time={"seconds": int(window_start.timestamp())},
    )

    results = monitoring.list_time_series(
        request={
            "name": project_name,
            "filter": (
                f'metric.type="compute.googleapis.com/instance/network/received_bytes_count" '
                f'AND resource.labels.instance_id="{instance.id}"'
            ),
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        }
    )

    total_bytes = sum(
        point.value.int64_value
        for series in results
        for point in series.points
    )

    logger.info(
        "Instance %s NetworkIn over last %d min: %d bytes",
        INSTANCE_NAME,
        IDLE_WINDOW_MINUTES,
        total_bytes,
    )

    # ── 3. Stop if idle ───────────────────────────────────────────────────────
    if total_bytes < IDLE_THRESHOLD_BYTES:
        logger.warning(
            "Instance %s is idle (%d bytes < %d threshold) — stopping",
            INSTANCE_NAME,
            total_bytes,
            IDLE_THRESHOLD_BYTES,
        )
        compute.stop(
            project=PROJECT_ID,
            zone=INSTANCE_ZONE,
            instance=INSTANCE_NAME,
        )
        return f"STOPPED {INSTANCE_NAME}: idle for {IDLE_WINDOW_MINUTES} min ({total_bytes} bytes)"

    return f"ACTIVE {INSTANCE_NAME}: {total_bytes} bytes in last {IDLE_WINDOW_MINUTES} min"
