"""Flat-file storage helpers"""
from pathlib import Path
from .settings import DATA_DIR


def data_path(*parts: str) -> Path:
    """Get a safe path within the data directory"""
    p = DATA_DIR.joinpath(*parts).resolve()
    if not str(p).startswith(str(DATA_DIR)):
        raise ValueError("Invalid path: attempted directory traversal")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def write_text(rel: str, text: str) -> str:
    """Write text to a flat file"""
    p = data_path(rel)
    p.write_text(text, encoding="utf-8")
    return str(p)


def read_text(rel: str) -> str:
    """Read text from a flat file"""
    p = data_path(rel)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def write_bytes(rel: str, data: bytes) -> str:
    """Write bytes to a flat file"""
    p = data_path(rel)
    p.write_bytes(data)
    return str(p)


def read_bytes(rel: str) -> bytes:
    """Read bytes from a flat file"""
    p = data_path(rel)
    return p.read_bytes() if p.exists() else b""


def exists(rel: str) -> bool:
    """Check if a flat file exists"""
    return data_path(rel).exists()


def delete(rel: str) -> bool:
    """Delete a flat file"""
    p = data_path(rel)
    if p.exists():
        p.unlink()
        return True
    return False
