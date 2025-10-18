"""Server-Sent Events (SSE) support"""
import asyncio
from .responses import sse_event, now_iso


async def sse_counter(scope, receive, send):
    """Example SSE endpoint that sends a counter every second"""
    assert scope["type"] == "http"

    headers = [
        (b"content-type", b"text/event-stream"),
        (b"cache-control", b"no-cache"),
        (b"connection", b"keep-alive"),
        (b"x-accel-buffering", b"no"),  # Disable nginx buffering
    ]

    await send({"type": "http.response.start", "status": 200, "headers": headers})

    i = 0
    try:
        while True:
            payload = sse_event(
                f'{{"count":{i},"ts":"{now_iso()}"}}', event="tick", id=str(i)
            )
            await send(
                {"type": "http.response.body", "body": payload, "more_body": True}
            )
            i += 1
            await asyncio.sleep(1.0)
    except asyncio.CancelledError:
        pass
    finally:
        await send({"type": "http.response.body", "body": b"", "more_body": False})


async def sse_stream(scope, receive, send, generator):
    """Generic SSE streaming from an async generator"""
    assert scope["type"] == "http"

    headers = [
        (b"content-type", b"text/event-stream"),
        (b"cache-control", b"no-cache"),
        (b"connection", b"keep-alive"),
        (b"x-accel-buffering", b"no"),
    ]

    await send({"type": "http.response.start", "status": 200, "headers": headers})

    try:
        async for event_data in generator:
            payload = sse_event(event_data)
            await send(
                {"type": "http.response.body", "body": payload, "more_body": True}
            )
    except asyncio.CancelledError:
        pass
    finally:
        await send({"type": "http.response.body", "body": b"", "more_body": False})
