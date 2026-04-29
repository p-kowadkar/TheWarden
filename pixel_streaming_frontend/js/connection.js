/**
 * connection.js
 *
 * WebRTC + signaling server logic for THE WARDEN Pixel Streaming frontend.
 *
 * Responsibilities:
 *   - Resolve the signaling server host from WARDEN_CONFIG or window.location.
 *   - Open a WSS connection to the UE5 Pixel Streaming signaling server (Cirrus).
 *   - Perform WebRTC offer/answer/ICE negotiation automatically.
 *   - Attach the incoming media stream to the <video> element.
 *   - Emit lifecycle events consumed by app.js.
 *   - Retry on disconnect (up to MAX_RETRIES, then emit 'fatal').
 *
 * Events emitted on the returned EventTarget:
 *   'connecting'     — signaling WebSocket opened
 *   'stream-ready'   — RTCPeerConnection has a live video track
 *   'disconnected'   — connection dropped; retry scheduled
 *   'reconnecting'   — retry attempt in progress
 *   'fatal'          — MAX_RETRIES exhausted
 *   'latency'        — { detail: { ms: number } } — RTT estimate every 2s
 */

const MAX_RETRIES        = 5;
const RETRY_INTERVAL_MS  = 10_000;
const LATENCY_INTERVAL_MS = 2_000;

/**
 * Resolve the WSS signaling URL.
 * Reads window.WARDEN_CONFIG.signalingHost if set and not a placeholder.
 * Falls back to wss://<current hostname>:443.
 */
function resolveSignalingUrl() {
  const cfg = window.WARDEN_CONFIG || {};
  const host = cfg.signalingHost;

  if (host && host !== '__SIGNALING_HOST__' && host.trim() !== '') {
    return `wss://${host}`;
  }
  return `wss://${window.location.hostname}:443`;
}

/**
 * Create and return a WardenConnection instance.
 *
 * @param {HTMLVideoElement} videoEl — the <video> element to attach the stream to
 * @returns {{ events: EventTarget, disconnect: () => void }}
 */
export function createConnection(videoEl) {
  const events = new EventTarget();

  let ws            = null;
  let pc            = null;
  let retryCount    = 0;
  let retryTimer    = null;
  let latencyTimer  = null;
  let destroyed     = false;

  // ── Latency estimation via RTCPeerConnection stats ──────────────────────
  function startLatencyPolling() {
    latencyTimer = setInterval(async () => {
      if (!pc) return;
      try {
        const stats = await pc.getStats();
        stats.forEach(report => {
          if (report.type === 'candidate-pair' && report.state === 'succeeded') {
            const rtt = report.currentRoundTripTime;
            if (rtt !== undefined) {
              events.dispatchEvent(
                new CustomEvent('latency', { detail: { ms: Math.round(rtt * 1000) } })
              );
            }
          }
        });
      } catch (_) { /* stats unavailable — ignore */ }
    }, LATENCY_INTERVAL_MS);
  }

  function stopLatencyPolling() {
    clearInterval(latencyTimer);
    latencyTimer = null;
  }

  // ── Cleanup helpers ──────────────────────────────────────────────────────
  function closeWebSocket() {
    if (ws) {
      ws.onopen = ws.onmessage = ws.onerror = ws.onclose = null;
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
      ws = null;
    }
  }

  function closePeerConnection() {
    stopLatencyPolling();
    if (pc) {
      pc.ontrack = pc.onicecandidate = pc.onconnectionstatechange = null;
      pc.close();
      pc = null;
    }
  }

  function scheduleRetry() {
    if (destroyed) return;

    retryCount += 1;
    if (retryCount > MAX_RETRIES) {
      events.dispatchEvent(new Event('fatal'));
      return;
    }

    events.dispatchEvent(new Event('disconnected'));

    retryTimer = setTimeout(() => {
      if (destroyed) return;
      events.dispatchEvent(new Event('reconnecting'));
      connect();
    }, RETRY_INTERVAL_MS);
  }

  // ── WebRTC setup ─────────────────────────────────────────────────────────
  function createPeerConnection() {
    const rtcConfig = {
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
    };

    pc = new RTCPeerConnection(rtcConfig);

    // Attach incoming media track to the video element
    pc.ontrack = (event) => {
      if (event.streams && event.streams[0]) {
        videoEl.srcObject = event.streams[0];
        videoEl.play().catch(() => {
          // Autoplay blocked — will be unblocked by first user interaction
        });
        events.dispatchEvent(new Event('stream-ready'));
        retryCount = 0; // Reset retry counter on successful stream
        startLatencyPolling();
      }
    };

    // Forward ICE candidates to the signaling server
    pc.onicecandidate = (event) => {
      if (event.candidate && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'iceCandidate',
          candidate: event.candidate,
        }));
      }
    };

    pc.onconnectionstatechange = () => {
      if (!pc) return;
      const state = pc.connectionState;
      if (state === 'failed' || state === 'closed') {
        closePeerConnection();
        closeWebSocket();
        scheduleRetry();
      }
    };
  }

  // ── Signaling ─────────────────────────────────────────────────────────────
  async function handleSignalingMessage(msg) {
    const data = JSON.parse(msg.data);

    switch (data.type) {
      case 'config':
        // Cirrus sends its config first — create the peer connection and offer
        createPeerConnection();
        try {
          const offer = await pc.createOffer({
            offerToReceiveAudio: true,
            offerToReceiveVideo: true,
          });
          await pc.setLocalDescription(offer);
          ws.send(JSON.stringify({ type: 'offer', sdp: offer.sdp }));
        } catch (err) {
          console.error('[connection] Failed to create offer:', err);
          closePeerConnection();
          scheduleRetry();
        }
        break;

      case 'answer':
        if (!pc) return;
        try {
          await pc.setRemoteDescription(
            new RTCSessionDescription({ type: 'answer', sdp: data.sdp })
          );
        } catch (err) {
          console.error('[connection] Failed to set remote description:', err);
        }
        break;

      case 'iceCandidate':
        if (!pc) return;
        try {
          await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
        } catch (err) {
          console.error('[connection] Failed to add ICE candidate:', err);
        }
        break;

      case 'playerCount':
      case 'peerDataChannels':
        // Informational messages from Cirrus — no action needed
        break;

      default:
        // Unknown message types are silently ignored
        break;
    }
  }

  // ── Main connect function ─────────────────────────────────────────────────
  function connect() {
    if (destroyed) return;

    closeWebSocket();
    closePeerConnection();

    const url = resolveSignalingUrl();
    console.info(`[connection] Connecting to ${url} (attempt ${retryCount + 1})`);

    try {
      ws = new WebSocket(url);
    } catch (err) {
      console.error('[connection] WebSocket construction failed:', err);
      scheduleRetry();
      return;
    }

    ws.onopen = () => {
      events.dispatchEvent(new Event('connecting'));
    };

    ws.onmessage = (msg) => {
      handleSignalingMessage(msg).catch(err => {
        console.error('[connection] Signaling message error:', err);
      });
    };

    ws.onerror = (err) => {
      console.error('[connection] WebSocket error:', err);
    };

    ws.onclose = (event) => {
      if (destroyed) return;
      console.warn(`[connection] WebSocket closed (code ${event.code})`);
      closePeerConnection();
      scheduleRetry();
    };
  }

  // ── Public API ────────────────────────────────────────────────────────────
  function disconnect() {
    destroyed = true;
    clearTimeout(retryTimer);
    stopLatencyPolling();
    closeWebSocket();
    closePeerConnection();
  }

  // Start immediately
  connect();

  return { events, disconnect };
}
