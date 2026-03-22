"""Download and install Stockfish engine locally for Day-02 chess project.

Usage:
    python setup_stockfish.py
"""

from __future__ import annotations

import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path


API_URL = "https://api.github.com/repos/official-stockfish/Stockfish/releases/latest"
PROJECT_DIR = Path(__file__).resolve().parent
TARGET_EXE = PROJECT_DIR / "stockfish.exe"


def fetch_latest_release() -> dict:
    req = urllib.request.Request(
        API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "day-02-chess-setup",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def pick_windows_asset(release: dict) -> tuple[str, str]:
    assets = release.get("assets", [])
    candidates = []
    for asset in assets:
        name = str(asset.get("name", "")).lower()
        url = str(asset.get("browser_download_url", ""))
        if not name.endswith(".zip"):
            continue
        if "windows" not in name and "win" not in name:
            continue
        candidates.append((name, url))

    if not candidates:
        raise RuntimeError("No Windows zip asset found in latest Stockfish release.")

    # Prefer AVX2 builds if available, then modern x86-64.
    def rank(item: tuple[str, str]) -> tuple[int, int]:
        name = item[0]
        return (
            0 if "avx2" in name else 1,
            0 if ("x86-64" in name or "x64" in name) else 1,
        )

    best_name, best_url = sorted(candidates, key=rank)[0]
    return best_name, best_url


def download_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "day-02-chess-setup"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()


def extract_engine(zip_blob: bytes) -> bytes:
    with zipfile.ZipFile(io.BytesIO(zip_blob)) as zf:
        exe_candidates = [
            name
            for name in zf.namelist()
            if name.lower().endswith(".exe") and "stockfish" in name.lower()
        ]
        if not exe_candidates:
            raise RuntimeError("Downloaded zip does not contain a Stockfish .exe file.")

        # Prefer shorter top-level binary name.
        exe_name = sorted(exe_candidates, key=lambda s: (s.count("/"), len(s)))[0]
        return zf.read(exe_name)


def main() -> int:
    print("Fetching latest Stockfish release metadata...")
    release = fetch_latest_release()
    asset_name, asset_url = pick_windows_asset(release)
    print(f"Selected asset: {asset_name}")

    print("Downloading engine zip (this can take a minute)...")
    zip_blob = download_bytes(asset_url)

    print("Extracting engine binary...")
    exe_blob = extract_engine(zip_blob)
    TARGET_EXE.write_bytes(exe_blob)

    print(f"Done. Installed: {TARGET_EXE}")
    print("You can now run: python chess_game.py")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"Setup failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
