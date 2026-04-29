/**
 * ui.js
 *
 * UI state management for THE WARDEN Pixel Streaming frontend.
 *
 * Manages transitions between:
 *   loading  — initial connecting screen
 *   stream   — full-screen game video
 *   error    — fatal connection failure screen
 *
 * Also manages:
 *   - Overlay visibility (Escape key toggle)
 *   - Status dot state (connected / reconnecting / disconnected)
 *   - Latency display
 *   - Status text transitions on the loading screen
 */

// ── DOM references ────────────────────────────────────────────────────────────

const loadingScreen  = document.getElementById('loading-screen');
const errorScreen    = document.getElementById('error-screen');
const streamContainer = document.getElementById('stream-container');
const statusText     = document.getElementById('status-text');
const errorText      = document.getElementById('error-text');
const overlay        = document.getElementById('overlay');
const latencyDisplay = document.getElementById('latency-display');
const statusDot      = document.getElementById('status-dot');
const disconnectBtn  = document.getElementById('disconnect-btn');

// ── State ─────────────────────────────────────────────────────────────────────

let overlayVisible = false;

// ── Internal helpers ──────────────────────────────────────────────────────────

/**
 * Update the status text on the loading screen.
 * Fades out the old text, swaps the content, fades in.
 * @param {string} text
 */
function setStatusText(text) {
  statusText.style.opacity = '0';
  setTimeout(() => {
    statusText.textContent = text;
    statusText.style.opacity = '1';
  }, 600);
}

/**
 * Set the status dot state.
 * @param {'connected'|'reconnecting'|'disconnected'} state
 */
function setDotState(state) {
  statusDot.className = 'status-dot';
  if (state === 'connected')    statusDot.classList.add('status-connected');
  if (state === 'reconnecting') statusDot.classList.add('status-reconnecting');
  if (state === 'disconnected') statusDot.classList.add('status-disconnected');
  statusDot.title = state.charAt(0).toUpperCase() + state.slice(1);
  statusDot.setAttribute('aria-label', `Connection status: ${state}`);
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Called when the signaling WebSocket first opens.
 * Updates status text; loading screen remains visible.
 */
export function onConnecting() {
  setStatusText('Establishing connection\u2026');
  setDotState('reconnecting');
}

/**
 * Called when the WebRTC stream is live and the video element has data.
 * Transitions: loading screen fades → stream container appears.
 */
export function onStreamReady() {
  setStatusText('Connected.');
  setDotState('connected');

  // Brief pause so "Connected." is readable, then fade to game
  setTimeout(() => {
    loadingScreen.classList.add('fading');

    setTimeout(() => {
      loadingScreen.classList.remove('active');
      loadingScreen.classList.add('hidden');
      streamContainer.classList.remove('hidden');
    }, 2500); // matches the CSS transition duration
  }, 1200);
}

/**
 * Called when the connection drops and a retry is scheduled.
 * Returns the user to the loading screen with a reconnect message.
 */
export function onDisconnected() {
  setDotState('disconnected');

  // If the stream was showing, return to loading screen
  if (!streamContainer.classList.contains('hidden')) {
    streamContainer.classList.add('hidden');
    loadingScreen.classList.remove('hidden', 'fading');
    loadingScreen.classList.add('active');
    hideOverlay();
  }

  setStatusText('Connection lost. Attempting to reconnect\u2026');
}

/**
 * Called at the start of each retry attempt.
 */
export function onReconnecting() {
  setDotState('reconnecting');
  setStatusText('Attempting to reconnect\u2026');
}

/**
 * Called when MAX_RETRIES is exhausted.
 * Shows the fatal error screen.
 */
export function onFatal() {
  loadingScreen.classList.remove('active');
  loadingScreen.classList.add('hidden');
  streamContainer.classList.add('hidden');
  errorScreen.classList.add('active');
  errorText.textContent = 'Unable to connect. The estate is unreachable.';
}

/**
 * Update the latency display in the overlay.
 * @param {number} ms
 */
export function updateLatency(ms) {
  latencyDisplay.textContent = `${ms}\u202fms`;
}

/**
 * Show the minimal overlay (Escape key).
 */
export function showOverlay() {
  overlayVisible = true;
  overlay.classList.remove('hidden');
  // requestAnimationFrame ensures the transition fires after display:block
  requestAnimationFrame(() => overlay.classList.add('visible'));
}

/**
 * Hide the minimal overlay.
 */
export function hideOverlay() {
  overlayVisible = false;
  overlay.classList.remove('visible');
  // Wait for CSS transition before hiding
  setTimeout(() => {
    if (!overlayVisible) overlay.classList.add('hidden');
  }, 2000);
}

/**
 * Toggle overlay visibility.
 */
export function toggleOverlay() {
  if (overlayVisible) {
    hideOverlay();
  } else {
    showOverlay();
  }
}

/**
 * Returns true if the overlay is currently visible.
 */
export function isOverlayVisible() {
  return overlayVisible;
}

/**
 * Bind the disconnect button callback.
 * @param {() => void} callback
 */
export function onDisconnectClick(callback) {
  disconnectBtn.addEventListener('click', callback);
}
