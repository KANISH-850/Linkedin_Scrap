import sys
from pathlib import Path

_backend_app_dir = Path(__file__).resolve().parent.parent / "backend" / "app"
if _backend_app_dir.exists():
    __path__.append(str(_backend_app_dir))

_backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

