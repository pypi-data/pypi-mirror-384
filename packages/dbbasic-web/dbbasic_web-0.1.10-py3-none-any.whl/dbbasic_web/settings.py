"""Application settings and configuration"""
import os
from pathlib import Path

# Allow override from environment or use current working directory if api/ exists
_cwd = Path.cwd()
if (_cwd / "api").exists() or (_cwd / "templates").exists():
    # Running from a project directory
    BASE_DIR = _cwd
    PROJECT_ROOT = _cwd.parent
else:
    # Running from installed package (fallback)
    BASE_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = BASE_DIR.parent

DEBUG = os.getenv("DEBUG", "1") == "1"

# Static / templates
TEMPLATES_DIR = BASE_DIR / "templates"
PUBLIC_DIR = BASE_DIR / "public"

# File storage root (flat files, TSV databases, job queues, event streams)
DATA_DIR = PROJECT_ROOT / "_data"
DATA_DIR.mkdir(exist_ok=True)

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
