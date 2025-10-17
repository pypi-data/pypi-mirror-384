import sys
import importlib.resources as resources
from pathlib import Path

_TOOLS = {
    "win32": {
        "libnedclib": "libnedclib.dll",
        "nedcenc": "nedcenc.exe",
        "nevpk": "nevpk.exe",
        "headerfix": "headerfix.exe"
    }
}

# validate platform os support
platform_tools = _TOOLS.get(sys.platform)
if not platform_tools:
    raise OSError(f"Piket currently does not support: {sys.platform}")

# resolve tool paths and expose them
_TOOL_PATHS: dict[str, Path] = {}
for tool, filename in platform_tools.items():
    try:
        with resources.path("piket.bin", filename) as p:
            if not Path(p).exists():
                raise FileNotFoundError(f"Missing required tool: {tool}")
            _TOOL_PATHS[tool] = p
    except Exception as e:
        raise ImportError(f"Error loading binary '{filename}': {e}")

NEDCENC = _TOOL_PATHS["nedcenc"]
NEVPK = _TOOL_PATHS["nevpk"]
HEADERFIX = _TOOL_PATHS["headerfix"]

# expose functions
from .main import decode_raw, encode_raw

__all__ = ["NEDCENC", "NEVPK", "HEADERFIX"]
