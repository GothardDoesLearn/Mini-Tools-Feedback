import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Nur Attribute, die der Browser selbst lädt (src, srcset, poster, data, url(), <link href>).
# Normale Links <a href="https://…"> sind erlaubt (z. B. Toolseite, Issue #13).
_EXTERN = r"""\s*["']?(?:https?:)?//"""
DRITTSERVER_RESSOURCE = re.compile(
    rf"""\b(?:src|srcset|poster|data)\s*={_EXTERN}|url\({_EXTERN}|<link\b[^>]*\bhref\s*={_EXTERN}""",
    re.IGNORECASE,
)


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


def test_ausgabe_enthaelt_keine_anfragen_an_drittserver(tmp_path: Path):
    run_build("--out", str(tmp_path / "dist"))

    for page in (tmp_path / "dist").rglob("*"):
        if page.suffix in {".html", ".css", ".js"}:
            assert not DRITTSERVER_RESSOURCE.search(page.read_text(encoding="utf-8")), page


def test_drittserver_pruefung_erkennt_ressourcen_aber_nicht_links():
    pattern = DRITTSERVER_RESSOURCE
    assert pattern.search('<img src="https://x.de/a.png">')
    assert pattern.search('<link rel="stylesheet" href="//fonts.example/x.css">')
    assert pattern.search("background: url('https://x.de/a.png')")
    assert not pattern.search('<a class="extern-link" href="https://www.oncoo.de">')
