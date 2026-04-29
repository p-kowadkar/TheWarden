/**
 * app.js
 *
 * Main entry point for THE WARDEN Pixel Streaming frontend.
 *
 * Responsibilities:
 *   - Wire connection.js events to ui.js state transitions.
 *   - Forward keyboard, mouse, and touch input to UE5 via the
 *     Pixel Streaming input protocol (data channel messages).
 *   - Manage pointer lock for mouse-look.
 *   - Handle Escape key to toggle the minimal overlay.
 */

import { createConnection } from './connection.js';
import {
  onConnecting,
  onStreamReady,
  onDisconnected,
  onReconnecting,
  onFatal,
  updateLatency,
  toggleOverlay,
  hideOverlay,
  isOverlayVisible,
  onDisconnectClick,
} from './ui.js';

// ── DOM references ────────────────────────────────────────────────────────────

const videoEl         = document.getElementById('stream-video');
const streamContainer = document.getElementById('stream-container');

// ── Connection ────────────────────────────────────────────────────────────────

let conn = null;

function startConnection() {
  conn = createConnection(videoEl);

  conn.events.addEventListener('connecting',   onConnecting);
  conn.events.addEventListener('stream-ready', handleStreamReady);
  conn.events.addEventListener('disconnected', onDisconnected);
  conn.events.addEventListener('reconnecting', onReconnecting);
  conn.events.addEventListener('fatal',        onFatal);
  conn.events.addEventListener('latency', (e) => updateLatency(e.detail.ms));
}

function handleStreamReady() {
  onStreamReady();
  bindInputForwarding();
}

// ── Disconnect button ─────────────────────────────────────────────────────────

onDisconnectClick(() => {
  if (conn) {
    conn.disconnect();
    conn = null;
  }
  onDisconnected();
  // Restart connection attempt
  startConnection();
});

// ── Escape key — overlay toggle ───────────────────────────────────────────────

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    // Release pointer lock when overlay appears
    if (!isOverlayVisible() && document.pointerLockElement) {
      document.exitPointerLock();
    }
    toggleOverlay();
    e.preventDefault();
  }
});

// ── Pointer lock ──────────────────────────────────────────────────────────────

videoEl.addEventListener('click', () => {
  if (isOverlayVisible()) return;
  if (!document.pointerLockElement) {
    videoEl.requestPointerLock();
  }
});

document.addEventListener('pointerlockchange', () => {
  if (!document.pointerLockElement) {
    // Pointer lock released — show overlay so the player can navigate
    if (!isOverlayVisible()) toggleOverlay();
  }
});

// ── Input forwarding to UE5 ───────────────────────────────────────────────────
//
// UE5 Pixel Streaming expects input via a WebRTC data channel.
// The signaling connection in connection.js does not yet expose the data
// channel — this is a scaffold for the developer to wire up once the
// RTCPeerConnection data channel negotiation is confirmed with the
// Cirrus signaling server version in use.
//
// Message format follows the UE5 Pixel Streaming input protocol:
//   https://docs.unrealengine.com/5.0/en-US/pixel-streaming-reference/
//
// The developer should:
//   1. In connection.js, expose the RTCDataChannel via a callback or event.
//   2. Replace sendInputMessage() below with actual data channel sends.

let dataChannel = null;

/**
 * Called by connection.js (developer TODO) when the data channel is ready.
 * @param {RTCDataChannel} dc
 */
export function setDataChannel(dc) {
  dataChannel = dc;
}

function sendInputMessage(data) {
  if (dataChannel && dataChannel.readyState === 'open') {
    dataChannel.send(data);
  }
}

// UE5 Pixel Streaming message type constants
const MessageType = {
  KeyDown:        0x00,
  KeyUp:          0x01,
  MouseEnter:     0x06,
  MouseLeave:     0x07,
  MouseMove:      0x08,
  MouseDown:      0x09,
  MouseUp:        0x0A,
  MouseWheel:     0x0B,
  TouchStart:     0x0C,
  TouchEnd:       0x0D,
  TouchMove:      0x0E,
};

function bindInputForwarding() {
  // ── Keyboard ──────────────────────────────────────────────────────────────
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') return; // Handled by overlay toggle above
    const buf = new Uint8Array(3);
    buf[0] = MessageType.KeyDown;
    buf[1] = e.keyCode & 0xFF;
    buf[2] = e.repeat ? 1 : 0;
    sendInputMessage(buf.buffer);
  });

  document.addEventListener('keyup', (e) => {
    if (e.key === 'Escape') return;
    const buf = new Uint8Array(2);
    buf[0] = MessageType.KeyUp;
    buf[1] = e.keyCode & 0xFF;
    sendInputMessage(buf.buffer);
  });

  // ── Mouse ─────────────────────────────────────────────────────────────────
  videoEl.addEventListener('mouseenter', () => {
    const buf = new Uint8Array(1);
    buf[0] = MessageType.MouseEnter;
    sendInputMessage(buf.buffer);
  });

  videoEl.addEventListener('mouseleave', () => {
    const buf = new Uint8Array(1);
    buf[0] = MessageType.MouseLeave;
    sendInputMessage(buf.buffer);
  });

  document.addEventListener('mousemove', (e) => {
    if (isOverlayVisible()) return;
    const buf = new DataView(new ArrayBuffer(9));
    buf.setUint8(0, MessageType.MouseMove);
    // Normalised position (0–65535) and delta
    buf.setUint16(1, Math.round((e.clientX / window.innerWidth)  * 65535), true);
    buf.setUint16(3, Math.round((e.clientY / window.innerHeight) * 65535), true);
    buf.setInt16(5, e.movementX, true);
    buf.setInt16(7, e.movementY, true);
    sendInputMessage(buf.buffer);
  });

  videoEl.addEventListener('mousedown', (e) => {
    if (isOverlayVisible()) return;
    const buf = new DataView(new ArrayBuffer(6));
    buf.setUint8(0, MessageType.MouseDown);
    buf.setUint8(1, e.button);
    buf.setUint16(2, Math.round((e.clientX / window.innerWidth)  * 65535), true);
    buf.setUint16(4, Math.round((e.clientY / window.innerHeight) * 65535), true);
    sendInputMessage(buf.buffer);
  });

  videoEl.addEventListener('mouseup', (e) => {
    const buf = new DataView(new ArrayBuffer(6));
    buf.setUint8(0, MessageType.MouseUp);
    buf.setUint8(1, e.button);
    buf.setUint16(2, Math.round((e.clientX / window.innerWidth)  * 65535), true);
    buf.setUint16(4, Math.round((e.clientY / window.innerHeight) * 65535), true);
    sendInputMessage(buf.buffer);
  });

  videoEl.addEventListener('wheel', (e) => {
    const buf = new DataView(new ArrayBuffer(3));
    buf.setUint8(0, MessageType.MouseWheel);
    buf.setInt16(1, Math.round(e.deltaY), true);
    sendInputMessage(buf.buffer);
    e.preventDefault();
  }, { passive: false });

  // Prevent right-click context menu over the stream
  videoEl.addEventListener('contextmenu', (e) => e.preventDefault());

  // ── Touch ─────────────────────────────────────────────────────────────────
  function encodeTouches(type, touches) {
    const count = Math.min(touches.length, 10);
    const buf = new DataView(new ArrayBuffer(2 + count * 7));
    buf.setUint8(0, type);
    buf.setUint8(1, count);
    for (let i = 0; i < count; i++) {
      const t = touches[i];
      const offset = 2 + i * 7;
      buf.setUint16(offset,     Math.round((t.clientX / window.innerWidth)  * 65535), true);
      buf.setUint16(offset + 2, Math.round((t.clientY / window.innerHeight) * 65535), true);
      buf.setUint8(offset + 4, t.identifier & 0xFF);
      buf.setUint8(offset + 5, Math.round(t.force * 255));
      buf.setUint8(offset + 6, 1); // valid
    }
    return buf.buffer;
  }

  videoEl.addEventListener('touchstart', (e) => {
    sendInputMessage(encodeTouches(MessageType.TouchStart, e.changedTouches));
    e.preventDefault();
  }, { passive: false });

  videoEl.addEventListener('touchend', (e) => {
    sendInputMessage(encodeTouches(MessageType.TouchEnd, e.changedTouches));
    e.preventDefault();
  }, { passive: false });

  videoEl.addEventListener('touchmove', (e) => {
    sendInputMessage(encodeTouches(MessageType.TouchMove, e.changedTouches));
    e.preventDefault();
  }, { passive: false });
}

// ── Boot ──────────────────────────────────────────────────────────────────────

startConnection();
