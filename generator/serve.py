"""Lokale Vorschau: liefert dist/ aus und baut bei Änderungen neu (nur Standardbibliothek)."""

import functools
import http.server
import threading
import time
import traceback
from collections.abc import Callable
from pathlib import Path

from generator.paths import CONFIG_FILE, CONTENT_DIR, STATIC_DIR, TEMPLATES_DIR

WATCHED = [CONFIG_FILE, CONTENT_DIR, TEMPLATES_DIR, STATIC_DIR]


def _snapshot() -> dict[Path, float]:
    files: dict[Path, float] = {}
    for item in WATCHED:
        candidates = [item] if item.is_file() else item.rglob("*") if item.exists() else []
        for f in candidates:
            if f.is_file():
                files[f] = f.stat().st_mtime
    return files


def _watch(rebuild: Callable[[], None], interval: float = 1.0) -> None:
    last = _snapshot()
    while True:
        time.sleep(interval)
        current = _snapshot()
        if current != last:
            last = current
            try:
                rebuild()
                print("Neu gebaut.")
            except Exception:
                traceback.print_exc()


def serve(output_dir: Path, rebuild: Callable[[], None], port: int = 8000) -> None:
    rebuild()
    threading.Thread(target=_watch, args=(rebuild,), daemon=True).start()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(output_dir))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Vorschau: http://127.0.0.1:{port}/  (Strg+C beendet)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
