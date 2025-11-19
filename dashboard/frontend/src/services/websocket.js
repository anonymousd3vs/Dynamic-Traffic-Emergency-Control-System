/**
 * WebSocket Service for Dashboard
 * Handles real-time communication with the backend server
 */

import { io } from 'socket.io-client';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 2000;
    this.listeners = new Map();
  }

  /**
   * Connect to the WebSocket server
   * Dynamically determines the correct host based on where the app is accessed from
   * @param {string} url - Server URL (optional, auto-detected if not provided)
   * @param {function} onConnect - Callback when connected
   * @param {function} onDisconnect - Callback when disconnected
   */
  connect(url, onConnect, onDisconnect) {
    // Prevent multiple concurrent connections
    if (this.socket && this.socket.connected) {
      console.log('WebSocket already connected, skipping reconnect');
      if (onConnect) onConnect();
      return;
    }

    // Close existing socket if it exists
    if (this.socket) {
      console.log('Closing existing WebSocket connection before reconnecting');
      this.socket.disconnect();
      this.socket = null;
    }

    // ✅ FIXED: Auto-detect correct WebSocket URL based on current host
    let wsUrl;
    if (url) {
      // Use provided URL if given
      wsUrl = url;
    } else {
      // Auto-detect: Use the same host as the frontend
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const hostname = window.location.hostname;
      const port = 8765;
      wsUrl = `${protocol}//${hostname}:${port}`;
    }

    console.log(`Connecting to WebSocket server at ${wsUrl}...`);

    this.socket = io(wsUrl, {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity,
      timeout: 10000,
      transports: ['websocket', 'polling'],
      upgrade: true,
      rememberUpgrade: true,
      pingTimeout: 120000,  // 2 minutes
      pingInterval: 30000,  // 30 seconds
      forceNew: true,
      autoConnect: true,
    });

    // Connection events
    this.socket.on('connect', () => {
      console.log('✅ WebSocket connected', this.socket.id);
      this.connected = true;
      this.reconnectAttempts = 0;
      if (onConnect) {
        console.log('Calling onConnect callback');
        onConnect();
      }
    });

    this.socket.on('disconnect', (reason) => {
      console.log(`❌ WebSocket disconnected: ${reason}`);
      this.connected = false;
      if (onDisconnect) {
        console.log('Calling onDisconnect callback');
        onDisconnect(reason);
      }
      
      // Attempt reconnection for certain reasons
      if (reason === 'io server disconnect') {
        console.log('Server initiated disconnect, attempting reconnection...');
        setTimeout(() => {
          if (!this.connected) {
            this.socket.connect();
          }
        }, 2000);
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error.message || error);
      console.error('Error details:', {
        type: error.type,
        description: error.description,
        context: error.context,
        transport: error.transport
      });
      this.reconnectAttempts++;
      
      // Show user-friendly error after multiple failures
      if (this.reconnectAttempts >= 5) {
        console.error('Multiple connection failures. Check if backend server is running.');
        console.error(`Tried connecting to: ${wsUrl}`);
        console.error('Make sure:');
        console.error('1. Backend server is running on port 8765');
        console.error('2. You can reach the host:', window.location.hostname);
        console.error('3. Firewall allows port 8765');
      }
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log(`✅ WebSocket reconnected after ${attemptNumber} attempts`);
    });

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`🔄 WebSocket reconnection attempt ${attemptNumber}`);
    });

    this.socket.on('reconnect_error', (error) => {
      console.error('WebSocket reconnection error:', error);
    });

    this.socket.on('reconnect_failed', () => {
      console.error('❌ WebSocket reconnection failed after maximum attempts');
    });

    // Server events
    this.socket.on('connection_established', (data) => {
      console.log('Connection established:', data);
    });

    // ✅ FIXED: Listen to correct event names from backend
    this.socket.on('metrics', (data) => {
      // Only log occasionally to reduce console spam
      this._notifyListeners('metrics', data);
    });

    // Keep backward compatibility with old event names
    this.socket.on('metrics_update', (data) => {
      this._notifyListeners('metrics', data);
    });

    this.socket.on('frame', (data) => {
      // Don't log every frame - that causes UI lag
      // Log only debug: console.debug('🎬 Frame received');
      this._notifyListeners('frame', data);
    });

    // Keep backward compatibility with old event names
    this.socket.on('frame_update', (data) => {
      this._notifyListeners('frame', data);
    });

    this.socket.on('alert', (data) => {
      console.log('🚨 Alert event received', data);
      this._notifyListeners('alert', data);
    });

    this.socket.on('server_status', (data) => {
      this._notifyListeners('status', data);
    });

    this.socket.on('pong', (data) => {
      console.log('Pong received:', data);
    });
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect() {
    if (this.socket) {
      console.log('Disconnecting from WebSocket server...');
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
  }

  /**
   * Subscribe to a specific event
   * @param {string} event - Event name ('metrics', 'frame', 'alert', 'status')
   * @param {function} callback - Callback function
   * @returns {function} Unsubscribe function
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.listeners.get(event);
      if (callbacks) {
        callbacks.delete(callback);
      }
    };
  }

  /**
   * Notify all listeners of an event
   * @param {string} event - Event name
   * @param {object} data - Event data
   */
  _notifyListeners(event, data) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in ${event} listener:`, error);
        }
      });
    }
  }

  /**
   * Send a ping to the server
   */
  ping() {
    if (this.socket && this.connected) {
      this.socket.emit('ping', { timestamp: Date.now() });
    }
  }

  /**
   * Request server status
   */
  requestStatus() {
    if (this.socket && this.connected) {
      this.socket.emit('request_status', {});
    }
  }

  /**
   * Get connection status
   * @returns {boolean}
   */
  isConnected() {
    return this.connected;
  }

  /**
   * Get the current WebSocket URL being used
   * @returns {string}
   */
  getServerUrl() {
    if (this.socket) {
      return this.socket.io.uri;
    }
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const hostname = window.location.hostname;
    const port = 8765;
    return `${protocol}//${hostname}:${port}`;
  }
}

// Create singleton instance
const wsService = new WebSocketService();

export default wsService;