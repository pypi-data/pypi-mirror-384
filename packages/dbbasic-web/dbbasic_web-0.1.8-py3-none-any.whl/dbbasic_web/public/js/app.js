// WebSocket test
let ws = null;

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/test`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        addMessage('ws-messages', 'Connected to WebSocket');
    };

    ws.onmessage = (event) => {
        addMessage('ws-messages', `Received: ${event.data}`);
    };

    ws.onerror = (error) => {
        addMessage('ws-messages', `Error: ${error.message}`);
    };

    ws.onclose = () => {
        addMessage('ws-messages', 'Disconnected from WebSocket');
    };
}

function sendMessage() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const message = { type: 'test', timestamp: new Date().toISOString(), message: 'Hello from client!' };
        ws.send(JSON.stringify(message));
        addMessage('ws-messages', `Sent: ${JSON.stringify(message)}`);
    } else {
        alert('WebSocket not connected');
    }
}

function disconnectWebSocket() {
    if (ws) {
        ws.close();
        ws = null;
    }
}

// SSE test
let eventSource = null;

function connectSSE() {
    eventSource = new EventSource('/sse/counter');

    eventSource.onopen = () => {
        addMessage('sse-messages', 'Connected to SSE');
    };

    eventSource.addEventListener('tick', (event) => {
        addMessage('sse-messages', `Tick: ${event.data}`);
    });

    eventSource.onerror = (error) => {
        addMessage('sse-messages', 'SSE error or connection closed');
        eventSource.close();
        eventSource = null;
    };
}

function disconnectSSE() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
        addMessage('sse-messages', 'Disconnected from SSE');
    }
}

// Helper function
function addMessage(containerId, message) {
    const container = document.getElementById(containerId);
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    messageDiv.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}
