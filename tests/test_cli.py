import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_build(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "build.py"), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_build_kommando_erzeugt_dist_mit_startseite(tmp_path: Path):
    result = run_build("--out", str(tmp_path / "dist"))

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "dist" / "index.html").is_file()


def test_check_prueft_ohne_zu_bauen(tmp_path: Path):
    result = run_build("--check", "--out", str(tmp_path / "dist"))

    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "dist").exists()


DRITTSERVER = re.compile(r"""(?:src|href|url)\s*[=(]\s*["']?(?:https?:)?//""", re.IGNORECASE)
# Normale Links (<a href>) laden nichts; erst der Klick des Nutzers verlässt die Seite.
LINK_TAG = re.compile(r"<a\s[^>]*>", re.IGNORECASE)


def test_ausgabe_enthaelt_keine_anfragen_an_drittserver(tmp_path: Path):
    run_build("--out", str(tmp_path / "dist"))

    for page in (tmp_path / "dist").rglob("*"):
        if page.suffix in {".html", ".css", ".js"}:
            text = LINK_TAG.sub("", page.read_text(encoding="utf-8"))
            assert not DRITTSERVER.search(text), page


def test_drittserver_pruefung_erlaubt_nur_normale_links():
    """Gegenprobe: Nur <a href> ist ausgenommen, eingebundene Ressourcen nicht."""
    assert not DRITTSERVER.search(LINK_TAG.sub("", '<a class="x" href="https://example.org/">'))
    assert DRITTSERVER.search(
        LINK_TAG.sub("", '<link rel="stylesheet" href="https://cdn.example/">')
    )
    assert DRITTSERVER.search(LINK_TAG.sub("", '<img src="//example.org/bild.png">'))
