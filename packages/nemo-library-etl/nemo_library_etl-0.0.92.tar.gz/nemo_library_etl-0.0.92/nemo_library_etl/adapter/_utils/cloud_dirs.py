import os
import platform
from pathlib import Path

def _first_existing(candidates):
    """Return the first existing path from a list of candidates."""
    for p in candidates:
        if p and Path(p).expanduser().exists():
            return str(Path(p).expanduser())
    return None

def find_onedrive_dir():
    """Try to locate the OneDrive folder on Windows, macOS, or Linux."""
    home = Path.home()
    system = platform.system()

    if system == "Windows":
        # Check environment variables (most reliable on Windows)
        env_candidates = [
            os.environ.get("OneDrive"),
            os.environ.get("OneDriveConsumer"),
            os.environ.get("OneDriveCommercial"),
        ]
        p = _first_existing(env_candidates)
        if p:
            return p

        # Fallback: check for OneDrive folders in home directory
        p = _first_existing([str(h) for h in home.glob("OneDrive*")])
        if p:
            return p

    if system == "Darwin":
        # macOS: OneDrive usually lives under CloudStorage
        p = _first_existing([
            "~/Library/CloudStorage/OneDrive",
        ] + [str(h) for h in Path("~/Library/CloudStorage").expanduser().glob("OneDrive*")])
        if p:
            return p

        # Fallback: legacy installs
        p = _first_existing([str(h) for h in home.glob("OneDrive*")])
        if p:
            return p

    # Linux or unknown system: heuristic only
    return _first_existing([str(h) for h in home.glob("OneDrive*")])



if __name__ == "__main__":
    print("OneDrive:", find_onedrive_dir())
