#!/usr/bin/env bash
# auto_shutdown.sh
# Monitors network ingress on the T4 GPU instance.
# If NetworkIn stays below 1 MB for 10 consecutive minutes, the instance
# shuts itself down to prevent unnecessary billing.
#
# Invoked every minute by cron (installed by startup.sh).
# State is persisted in /tmp/warden_idle_count.

set -euo pipefail

IDLE_THRESHOLD_MB=1
IDLE_LIMIT_MINUTES=10
STATE_FILE="/tmp/warden_idle_count"
NETWORK_INTERFACE="eth0"

# ── Read bytes received in the last 60 seconds ───────────────────────────────
# /proc/net/dev columns: iface | rx_bytes rx_packets ... | tx_bytes ...
RX_BYTES_NOW=$(awk -v iface="${NETWORK_INTERFACE}:" '$1==iface {print $2}' /proc/net/dev)
sleep 60
RX_BYTES_AFTER=$(awk -v iface="${NETWORK_INTERFACE}:" '$1==iface {print $2}' /proc/net/dev)

DELTA_BYTES=$(( RX_BYTES_AFTER - RX_BYTES_NOW ))
DELTA_MB=$(( DELTA_BYTES / 1048576 ))

echo "[auto_shutdown] $(date) — NetworkIn delta: ${DELTA_MB} MB"

# ── Update idle counter ───────────────────────────────────────────────────────
if [ "$DELTA_MB" -lt "$IDLE_THRESHOLD_MB" ]; then
  IDLE_COUNT=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
  IDLE_COUNT=$(( IDLE_COUNT + 1 ))
  echo "$IDLE_COUNT" > "$STATE_FILE"
  echo "[auto_shutdown] Idle minute count: ${IDLE_COUNT}/${IDLE_LIMIT_MINUTES}"

  if [ "$IDLE_COUNT" -ge "$IDLE_LIMIT_MINUTES" ]; then
    echo "[auto_shutdown] Idle limit reached — initiating shutdown"
    # Retrieve instance metadata for self-identification
    INSTANCE_NAME=$(curl -sf \
      "http://metadata.google.internal/computeMetadata/v1/instance/name" \
      -H "Metadata-Flavor: Google")
    ZONE=$(curl -sf \
      "http://metadata.google.internal/computeMetadata/v1/instance/zone" \
      -H "Metadata-Flavor: Google" | awk -F/ '{print $NF}')

    gcloud compute instances stop "$INSTANCE_NAME" --zone="$ZONE" --quiet
  fi
else
  # Activity detected — reset counter
  echo 0 > "$STATE_FILE"
  echo "[auto_shutdown] Activity detected — idle counter reset"
fi
