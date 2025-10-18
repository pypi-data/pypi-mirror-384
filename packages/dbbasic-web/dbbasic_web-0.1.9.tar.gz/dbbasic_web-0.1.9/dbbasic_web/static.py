"""Static file serving"""
import mimetypes
from pathlib import Path
from .settings import PUBLIC_DIR


def serve_static(path: str):
    """Serve a static file from the public directory"""
    # Sanitize and resolve path
    clean_path = path.strip("/")
    if not clean_path:
        return 404, [("content-type", "text/plain")], [b"Not Found"]

    candidate = (PUBLIC_DIR / clean_path).resolve()

    # Security: ensure we're still inside PUBLIC_DIR
    if not str(candidate).startswith(str(PUBLIC_DIR)):
        return 403, [("content-type", "text/plain")], [b"Forbidden"]

    if not candidate.exists() or not candidate.is_file():
        return 404, [("content-type", "text/plain")], [b"Not Found"]

    ctype, _ = mimetypes.guess_type(str(candidate))
    ctype = ctype or "application/octet-stream"

    return 200, [("content-type", ctype)], [candidate.read_bytes()]
