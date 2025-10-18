"""ASGI application - the heart of dbbasic-web"""
import json
from .router import route
from .sse import sse_counter
from .websocket import hub


async def app(scope, receive, send):
    """Main ASGI application"""

    if scope["type"] == "http":
        await http_handler(scope, receive, send)
    elif scope["type"] == "websocket":
        await websocket_handler(scope, receive, send)
    elif scope["type"] == "lifespan":
        await lifespan_handler(scope, receive, send)


async def http_handler(scope, receive, send):
    """Handle HTTP requests"""
    path = scope["path"]

    # Special routes for SSE
    if path == "/sse/counter":
        await sse_counter(scope, receive, send)
        return

    # Read request body for POST/PUT requests
    body = b""
    while True:
        message = await receive()
        if message["type"] == "http.request":
            body += message.get("body", b"")
            if not message.get("more_body", False):
                break
        elif message["type"] == "http.disconnect":
            return

    # Normal routing through filesystem router
    status, headers, body_parts = route(scope, body)

    # Convert to ASGI format
    headers_asgi = [(k.encode() if isinstance(k, str) else k,
                     v.encode() if isinstance(v, str) else v)
                    for k, v in headers]

    await send({
        "type": "http.response.start",
        "status": status,
        "headers": headers_asgi,
    })

    for part in body_parts:
        await send({
            "type": "http.response.body",
            "body": part if isinstance(part, bytes) else part.encode(),
        })


async def websocket_handler(scope, receive, send):
    """Handle WebSocket connections"""
    await send({"type": "websocket.accept"})

    # Extract room from path or query string
    path = scope["path"]
    room = path.split("/")[-1] if "/" in path else "default"

    # Create a simple wrapper for the WebSocket
    class WSWrapper:
        async def send_text(self, message):
            await send({"type": "websocket.send", "text": message})

    ws = WSWrapper()
    await hub.join(room, ws)

    try:
        while True:
            message = await receive()

            if message["type"] == "websocket.disconnect":
                break

            if message["type"] == "websocket.receive":
                # Echo or broadcast received messages
                if "text" in message:
                    try:
                        data = json.loads(message["text"])
                        await hub.broadcast(room, data)
                    except json.JSONDecodeError:
                        await ws.send_text(json.dumps({"error": "Invalid JSON"}))

    finally:
        await hub.leave(room, ws)


async def lifespan_handler(scope, receive, send):
    """Handle application lifecycle events"""
    while True:
        message = await receive()

        if message["type"] == "lifespan.startup":
            # Startup logic here (open database connections, etc.)
            await send({"type": "lifespan.startup.complete"})

        elif message["type"] == "lifespan.shutdown":
            # Shutdown logic here (close connections, etc.)
            await send({"type": "lifespan.shutdown.complete"})
            return
