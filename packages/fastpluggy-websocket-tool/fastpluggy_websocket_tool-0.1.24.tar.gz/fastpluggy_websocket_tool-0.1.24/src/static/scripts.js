// main-thread.js - Enhanced WebSocket client integration

// ------------------------------------------------------
// 🔧 Client ID Management
// ------------------------------------------------------
function getClientId() {
    let id = localStorage.getItem('clientId');
    if (!id) {
        id = crypto.randomUUID();
        localStorage.setItem('clientId', id);
    }
    return id;
}

// ------------------------------------------------------
// 🔄 WebSocket Initialization Helper
// ------------------------------------------------------
function sendInit() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    const wsUrl = `${wsProtocol}//${wsHost}/ws`;
    const clientId = getClientId();

    // Use the unified sendServiceWorkerMessage function
    window.sendServiceWorkerMessage('INIT_WEBSOCKET', {
        wsUrl: wsUrl,
        clientId: clientId
    });

    console.log("[SW] Init WebSocket (with clientId) sent", clientId);
}

function initWebSocket() {
    if (navigator.serviceWorker.controller) {
        sendInit();
    } else {
        console.warn("[SW] Controller not ready, attempting claim...");

        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.ready.then(registration => {
                if (registration.active) {
                    // Use the unified sendServiceWorkerMessage function
                    // Note: We need to use registration.active here since controller isn't available yet
                    registration.active.postMessage({ type: 'CLAIM_CLIENTS' });
                    console.log("[SW] Sent CLAIM_CLIENTS message");

                    setTimeout(() => {
                        if (navigator.serviceWorker.controller) {
                            sendInit();
                        } else {
                            console.warn("[SW] Controller still not ready");
                        }
                    }, 500);
                }
            });
        }
    }
}

function initWebSocketWithRetry(maxRetries = 3, baseDelay = 1000) {
    let retryCount = 0;

    function attemptInit() {
        if (navigator.serviceWorker.controller) {
            sendInit();
            return true;
        } else if (retryCount < maxRetries) {
            retryCount++;
            const delay = baseDelay * Math.pow(2, retryCount - 1);
            console.log(`[SW] Controller not ready, retrying in ${delay}ms (attempt ${retryCount}/${maxRetries})`);

            setTimeout(attemptInit, delay);
            return false;
        } else {
            console.warn("[SW] Controller not ready after all retries");
            return false;
        }
    }

    attemptInit();
}

// ------------------------------------------------------
// 🚀 Enhanced Service Worker Registration
// ------------------------------------------------------
async function initServiceWorkerWithVersionControl() {
    if (!('serviceWorker' in navigator)) {
        console.error("[SW] Not supported in this browser.");
        return;
    }

    try {
        const versionSuffix = window.SW_VERSION ? `?v=${window.SW_VERSION}` : "";
        const swPath = `/service-worker.js${versionSuffix}`;

        // Register service worker
        const registration = await navigator.serviceWorker.register(swPath, { scope: '/' });
        console.log("[SW] Registered:", registration.scope);

        // Wait for service worker to be ready
        await navigator.serviceWorker.ready;
        setTimeout(() => initWebSocketWithRetry(), 100);

    } catch (error) {
        console.error("[SW] Registration failed:", error);
    }

    // Listen for controller changes
    navigator.serviceWorker.addEventListener('controllerchange', () => {
        console.log("[SW] Controller changed, initializing WebSocket");
        setTimeout(() => initWebSocket(), 100);
    });
}

// ------------------------------------------------------
// 📬 Enhanced Service Worker Message Handling
// ------------------------------------------------------
navigator.serviceWorker.addEventListener('message', event => {
    const eventData = event.data;

    if (eventData.type === 'WEBSOCKET_MESSAGE') {
        // Regular WebSocket messages (ping/pong filtered out by service worker)
        const data = eventData.data;

        if (window.WebSocketRegistry && typeof window.WebSocketRegistry.emit === 'function') {
            window.WebSocketRegistry.emit(data);
        } else {
            console.warn("[WebSocket] WebSocketRegistry not ready or invalid:", data);
        }
    }

    else if (eventData.type === 'WEBSOCKET_STATUS') {
        // Connection status updates
        console.log(`[WebSocket] Status: ${eventData.status}`);

        if (eventData.status === 'connected') {
            console.log("[WebSocket] ✅ Connected via service worker");
            updateConnectionStatus(true);
        } else if (eventData.status === 'disconnected') {
            console.warn("[WebSocket] ❌ Disconnected via service worker");
            updateConnectionStatus(false);

            // Show ping/pong stats on disconnect
            if (eventData.pingStats) {
                console.log("[WebSocket] Final ping/pong stats:", eventData.pingStats);
            }
        }
    }

    else if (eventData.type === 'WEBSOCKET_HEALTH') {
        // Connection health updates
        console.log(`[WebSocket] Health: ${eventData.status}`);
        updateConnectionHealth(eventData.status === 'healthy');
    }
});


// ------------------------------------------------------
// 📢 Enhanced Toast Notification
// ------------------------------------------------------
function showNotification(message, level = "info", link = null) {
    const container = document.getElementById("notifications");

    if (!container) {
        console.warn("[Notification] Container not found");
        return;
    }

    const levelClasses = {
        info: "bg-primary text-white",
        warning: "bg-warning text-dark",
        error: "bg-danger text-white",
        success: "bg-success text-white"
    };
    const colorClass = levelClasses[level] || "bg-primary text-white";

    const textNode = document.createElement("div");
    textNode.appendChild(document.createTextNode(message));
    const escapedMessage = textNode.innerHTML;

    const notification = document.createElement("div");
    notification.className = `toast show mb-3 ${colorClass}`;
    notification.role = "alert";

    let toastContent = `
        <div class="toast-header">
            <strong class="me-auto">Task Update</strong>
            <button type="button" class="btn-close ms-2 mb-1" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">${escapedMessage}
    `;

    if (link) {
        toastContent += `
            <div class="mt-2">
                <a href="${link}" target="_blank" class="text-white text-decoration-underline">View details</a>
            </div>
        `;
    }

    toastContent += `</div>`;
    notification.innerHTML = toastContent;

    container.appendChild(notification);

    // Auto-remove notification after 5 seconds
    setTimeout(() => {
        if (container.contains(notification)) {
            container.removeChild(notification);
        }
    }, 5000);

    // Handle manual close button
    const closeButton = notification.querySelector('.btn-close');
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            if (container.contains(notification)) {
                container.removeChild(notification);
            }
        });
    }
}

// ------------------------------------------------------
// 💬 Register Default Message Handlers
// ------------------------------------------------------

// Main business logic handlers
safeRegisterHandler("message", (data) => {
    showNotification(data.content, data.meta?.level, data.meta?.link);
});

safeRegisterHandler("task_update", (data) => {
    const taskId = data.meta?.task_id;
    const status = data.meta?.status;

    console.log(`[Task] ${taskId}: ${status} - ${data.content}`);
    showNotification(data.content, data.meta?.level);
});

safeRegisterHandler("admin_message", (data) => {
    showNotification(`Admin: ${data.content}`, data.meta?.level || "warning");
});

// ------------------------------------------------------
// 🔧 Utility Functions
// ------------------------------------------------------

function updateConnectionStatus(isConnected) {
    const statusElement = document.getElementById('ws-connection-status');
    if (statusElement) {
        statusElement.textContent = isConnected ? 'Connected' : 'Disconnected';
        statusElement.className = isConnected ? 'status-connected' : 'status-disconnected';
    }

    // Update any connection indicators
    document.body.setAttribute('data-websocket-connected', isConnected);
}

function updateConnectionHealth(isHealthy) {
    const healthElement = document.getElementById('ws-connection-health');
    if (healthElement) {
        healthElement.textContent = isHealthy ? 'Healthy' : 'Unhealthy';
        healthElement.className = isHealthy ? 'health-good' : 'health-poor';
    }
}

// Get ping/pong stats from service worker
async function getPingPongStats() {
    if (!navigator.serviceWorker.controller) {
        return null;
    }

    // Use the unified sendServiceWorkerMessage function with waitForResponse=true
    const response = await window.sendServiceWorkerMessage('GET_PING_STATS', {}, true);

    // Return the stats if available
    return response && response.type === 'PING_STATS_RESPONSE' ? response.stats : null;
}

// Display connection stats in console
async function showConnectionStats() {
    const stats = await getPingPongStats();

    if (stats) {
        console.log("📊 WebSocket Ping/Pong Stats:", {
            "Pings received": stats.pingCount,
            "Pongs sent": stats.pongCount,
            "Average response time": `${stats.averageResponseTime.toFixed(2)}ms`,
            "Last ping": new Date(stats.lastPingReceived).toLocaleTimeString(),
            "Last pong": new Date(stats.lastPongSent).toLocaleTimeString()
        });
    }
}

// ------------------------------------------------------
// 🔧 Initialize Everything
// ------------------------------------------------------
fetch("/sw_info.json")
    .then(res => res.json())
    .then(data => {
        window.SW_VERSION = data.version;
        console.log("[SW] Loaded version:", window.SW_VERSION);
        initServiceWorkerWithVersionControl();
    })
    .catch(err => {
        console.warn("[SW] Failed to fetch version:", err);
        initServiceWorkerWithVersionControl();
    });

// Optional: Add global function to show stats
window.showWebSocketStats = showConnectionStats;
