#!/usr/bin/env bash
# startup.sh
# T4 GPU instance startup script for THE WARDEN Pixel Streaming.
#
# Executed once when the instance boots. Installs dependencies, configures the
# Node.js signaling server, and launches Unreal Engine 5 in headless Pixel
# Streaming mode.
#
# Prerequisites baked into the base image:
#   - NVIDIA T4 drivers (CUDA 12.x)
#   - Unreal Engine 5.7 installed at C:\UE5 (Windows) or /opt/UE5 (Linux)
#   - The Warden packaged build at /opt/warden/TheWarden
#
# This script targets Linux. If the base image is Windows, convert to
# PowerShell and adjust paths accordingly.

set -euo pipefail

LOG="/var/log/warden-startup.log"
exec > >(tee -a "$LOG") 2>&1

echo "[startup] $(date) — Warden Pixel Streaming startup beginning"

# ── 1. Install Node.js (if not present) ──────────────────────────────────────
if ! command -v node &>/dev/null; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

echo "[startup] Node.js $(node --version) ready"

# ── 2. Install / update the UE5 Pixel Streaming signaling server ─────────────
SIGNAL_DIR="/opt/warden/signaling"
mkdir -p "$SIGNAL_DIR"

if [ ! -f "$SIGNAL_DIR/package.json" ]; then
  # Copy the signaling server bundled with the packaged build
  cp -r /opt/warden/TheWarden/Samples/PixelStreaming/WebServers/SignallingWebServer/. "$SIGNAL_DIR/"
fi

cd "$SIGNAL_DIR"
npm install --omit=dev

echo "[startup] Signaling server dependencies installed"

# ── 3. Obtain a TLS certificate (self-signed for scaffold; replace with ACM) ─
CERT_DIR="/etc/warden/ssl"
mkdir -p "$CERT_DIR"

if [ ! -f "$CERT_DIR/cert.pem" ]; then
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$CERT_DIR/key.pem" \
    -out    "$CERT_DIR/cert.pem" \
    -subj   "/CN=warden-pixel-streaming"
  echo "[startup] Self-signed TLS certificate generated"
fi

# ── 4. Launch the signaling server ───────────────────────────────────────────
node "$SIGNAL_DIR/cirrus.js" \
  --publicIp="$(curl -sf http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H 'Metadata-Flavor: Google')" \
  --httpsPort=443 \
  --httpPort=80 \
  --streamerPort=8888 \
  --sslKeyPath="$CERT_DIR/key.pem" \
  --sslCertPath="$CERT_DIR/cert.pem" \
  &

echo "[startup] Signaling server launched (PID $!)"

# ── 5. Launch Unreal Engine 5 in headless Pixel Streaming mode ───────────────
UE_BINARY="/opt/warden/TheWarden/Binaries/Linux/TheWarden-Linux-Shipping"

if [ ! -f "$UE_BINARY" ]; then
  echo "[startup] ERROR: UE5 binary not found at $UE_BINARY — aborting"
  exit 1
fi

"$UE_BINARY" \
  -RenderOffscreen \
  -PixelStreamingIP=localhost \
  -PixelStreamingPort=8888 \
  -AudioMixer \
  -NullRHI=false \
  -ResX=1920 -ResY=1080 \
  &

echo "[startup] Unreal Engine launched (PID $!)"

# ── 6. Install the auto-shutdown watchdog ────────────────────────────────────
SHUTDOWN_SCRIPT="/opt/warden/auto_shutdown.sh"
cp "$(dirname "$0")/auto_shutdown.sh" "$SHUTDOWN_SCRIPT"
chmod +x "$SHUTDOWN_SCRIPT"

# Run watchdog every minute via cron
(crontab -l 2>/dev/null; echo "* * * * * $SHUTDOWN_SCRIPT >> /var/log/warden-shutdown.log 2>&1") | crontab -

echo "[startup] Auto-shutdown watchdog installed"
echo "[startup] $(date) — Startup complete"
