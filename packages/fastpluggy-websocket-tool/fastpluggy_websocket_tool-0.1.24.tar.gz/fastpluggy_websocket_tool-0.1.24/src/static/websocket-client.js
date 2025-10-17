/**
 * websocket-client.js - WebSocket client utilities for FastPluggy
 * 
 * This file provides utilities for WebSocket communication in the browser:
 * - WebSocketRegistry: A registry for WebSocket message handlers
 * - safeRegisterHandler: A function to safely register handlers even if the registry isn't loaded yet
 * - sendWebSocketMessage: A function to send messages through a WebSocket connection
 */

(function() {
    // Initialize queue for early registrations
    if (!window.__WebSocketRegistryQueue) {
        window.__WebSocketRegistryQueue = [];
    }

    /**
     * WebSocketRegistry - A registry for WebSocket message handlers
     */
    const WebSocketRegistry = {
        handlers: {},

        /**
         * Register a handler for a specific message type
         * @param {string} type - The message type to handle
         * @param {function} callback - The handler function
         */
        registerHandler(type, callback) {
            if (!this.handlers[type]) {
                this.handlers[type] = [];
            }
            console.log(`[WebSocket] Handler registered for "${type}"`);
            this.handlers[type].push(callback);
        },

        /**
         * Emit a message to all registered handlers for its type
         * @param {object} message - The message object with type property
         */
        emit(message) {
            const type = message.type || message.meta?.event;
            if (this.handlers[type]) {
                this.handlers[type].forEach(cb => cb(message));
            }
        },

        /**
         * Clear handlers for a specific type or all types
         * @param {string|null} type - The message type to clear, or null for all
         */
        clearHandlers(type = null) {
            if (type) {
                delete this.handlers[type];
            } else {
                this.handlers = {};
            }
        },

        /**
         * Get all registered message types
         * @returns {string[]} Array of registered message types
         */
        getRegisteredTypes() {
            return Object.keys(this.handlers);
        }
    };

    /**
     * Safely register a handler, even if WebSocketRegistry isn't loaded yet
     * @param {string} type - The message type to handle
     * @param {function} callback - The handler function
     */
    function safeRegisterHandler(type, callback) {
        if (window.WebSocketRegistry) {
            window.WebSocketRegistry.registerHandler(type, callback);
        } else {
            if (!window.__WebSocketRegistryQueue) {
                window.__WebSocketRegistryQueue = [];
            }
            window.__WebSocketRegistryQueue.push({ type, callback });
        }
    }

    // Process any handlers that were registered before this script loaded
    function flushQueue() {
        if (window.__WebSocketRegistryQueue && window.__WebSocketRegistryQueue.length > 0) {
            console.log(`[WebSocket] Processing ${window.__WebSocketRegistryQueue.length} queued handlers`);
            while (window.__WebSocketRegistryQueue.length > 0) {
                const { type, callback } = window.__WebSocketRegistryQueue.shift();
                WebSocketRegistry.registerHandler(type, callback);
            }
        }
    }

    /**
     * Send a message through a WebSocket connection
     * @param {WebSocket} socket - The WebSocket connection to send through
     * @param {string} type - The message type
     * @param {object} data - The data to send
     * @returns {boolean} - Whether the message was sent successfully
     */
    function sendWebSocketMessage(socket, type, data = {}) {
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            console.error('[WebSocket] Cannot send message: socket is not open');
            return false;
        }

        try {
            const message = {
                type: type,
                ...data
            };
            socket.send(JSON.stringify(message));
            console.log(`[WebSocket] Sent message of type "${type}"`);
            return true;
        } catch (error) {
            console.error('[WebSocket] Error sending message:', error);
            return false;
        }
    }

    /**
     * Send a message to the service worker
     * @param {string} type - The message type
     * @param {object} data - The data to send
     * @param {boolean} waitForResponse - Whether to wait for a response from the service worker
     * @returns {Promise<any>|boolean} - A promise that resolves with the response if waitForResponse is true, otherwise a boolean indicating success
     */
    function sendServiceWorkerMessage(type, data = {}, waitForResponse = false) {
        if (!navigator.serviceWorker || !navigator.serviceWorker.controller) {
            console.error('[ServiceWorker] Cannot send message: Service Worker not available');
            return waitForResponse ? Promise.resolve(null) : false;
        }

        // For messages that need to be sent through the WebSocket
        if (type === 'SEND_WS_MESSAGE') {
            return sendServiceWorkerWebSocketMessage(data.messageType, data.messageData, waitForResponse);
        }

        try {
            // Create a message to send to the service worker
            const message = {
                type: type,
                ...data
            };

            if (waitForResponse) {
                // Create a message channel for the response
                const messageChannel = new MessageChannel();

                // Create a promise that will be resolved when we get a response
                const responsePromise = new Promise((resolve) => {
                    messageChannel.port1.onmessage = (event) => {
                        resolve(event.data);
                    };

                    // Set a timeout in case we don't get a response
                    setTimeout(() => resolve(null), 1000);
                });

                // Send the message to the service worker with the message channel
                navigator.serviceWorker.controller.postMessage(message, [messageChannel.port2]);

                return responsePromise;
            } else {
                // Send the message to the service worker without waiting for a response
                navigator.serviceWorker.controller.postMessage(message);
                return true;
            }
        } catch (error) {
            console.error('[ServiceWorker] Error sending message:', error);
            return waitForResponse ? Promise.resolve(null) : false;
        }
    }

    /**
     * Send a message through the service worker's WebSocket connection
     * @param {string} type - The message type
     * @param {object} data - The data to send
     * @param {boolean} waitForResponse - Whether to wait for a response from the service worker
     * @returns {Promise<boolean>|boolean} - A promise that resolves with a boolean indicating success if waitForResponse is true, otherwise a boolean indicating success
     */
    function sendServiceWorkerWebSocketMessage(type, data = {}, waitForResponse = false) {
        if (!navigator.serviceWorker || !navigator.serviceWorker.controller) {
            console.error('[ServiceWorker] Cannot send WebSocket message: Service Worker not available');
            return waitForResponse ? Promise.resolve(false) : false;
        }

        try {
            // Create a message channel for the response
            const messageChannel = new MessageChannel();

            if (waitForResponse) {
                // Create a promise that will be resolved when we get a response
                const responsePromise = new Promise((resolve) => {
                    messageChannel.port1.onmessage = (event) => {
                        if (event.data && event.data.type === 'SEND_WS_MESSAGE_RESPONSE') {
                            resolve(event.data.success);
                        } else {
                            resolve(false);
                        }
                    };

                    // Set a timeout in case we don't get a response
                    setTimeout(() => resolve(false), 1000);
                });

                // Send the message to the service worker
                navigator.serviceWorker.controller.postMessage({
                    type: 'SEND_WS_MESSAGE',
                    messageType: type,
                    messageData: data
                }, [messageChannel.port2]);

                return responsePromise;
            } else {
                // Send the message to the service worker without waiting for a response
                navigator.serviceWorker.controller.postMessage({
                    type: 'SEND_WS_MESSAGE',
                    messageType: type,
                    messageData: data
                }, [messageChannel.port2]);

                return true;
            }
        } catch (error) {
            console.error('[ServiceWorker] Error sending WebSocket message:', error);
            return waitForResponse ? Promise.resolve(false) : false;
        }
    }

    // Register globally
    window.WebSocketRegistry = WebSocketRegistry;
    window.safeRegisterHandler = safeRegisterHandler;
    window.sendWebSocketMessage = sendWebSocketMessage;
    window.sendServiceWorkerMessage = sendServiceWorkerMessage;
    window.sendServiceWorkerWebSocketMessage = sendServiceWorkerWebSocketMessage;

    // Process any queued handlers
    flushQueue();
})();
