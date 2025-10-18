"""Response helpers for various content types"""
from typing import Iterable
from datetime import datetime


def html(body: str, status: int = 200, headers: list[tuple[str, str]] | None = None):
    """Return HTML response"""
    h = [("content-type", "text/html; charset=utf-8")]
    if headers:
        h.extend(headers)
    return status, h, [body.encode("utf-8")]


def json(body: bytes | str, status: int = 200, headers: list[tuple[str, str]] | None = None):
    """Return JSON response"""
    h = [("content-type", "application/json; charset=utf-8")]
    if headers:
        h.extend(headers)
    b = body if isinstance(body, bytes) else body.encode("utf-8")
    return status, h, [b]


def json_error(message: str, status: int = 404):
    """
    Return JSON error response.

    Convenience helper that reduces verbose error handling:

    Before:
        import json as json_lib
        return json(json_lib.dumps({"error": "User not found"}), status=404)

    After:
        return json_error("User not found", status=404)

    Example:
        from dbbasic_web.responses import json_error

        def handle(request):
            user_id = request.path_param(1)
            if not user_id:
                return json_error("User ID required", status=400)

            user = get_user(user_id)
            if not user:
                return json_error("User not found", status=404)

            return json(...)
    """
    import json as json_lib
    return json(json_lib.dumps({"error": message}), status=status)


def text(s: str, status: int = 200):
    """Return plain text response"""
    return status, [("content-type", "text/plain; charset=utf-8")], [s.encode("utf-8")]


def redirect(location: str, status: int = 302):
    """Return redirect response"""
    return status, [("location", location)], [b""]


def sse_event(data: str, event: str | None = None, id: str | None = None) -> bytes:
    """Format a Server-Sent Event"""
    lines = []
    if event:
        lines.append(f"event: {event}")
    if id:
        lines.append(f"id: {id}")
    for line in data.splitlines() or [""]:
        lines.append(f"data: {line}")
    lines.append("")  # final newline
    return ("\n".join(lines) + "\n").encode("utf-8")


def now_iso() -> str:
    """Return current UTC time in ISO format"""
    return datetime.utcnow().isoformat() + "Z"
