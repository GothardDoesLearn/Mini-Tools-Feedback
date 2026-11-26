"""Link-Check über den gesamten Build (Issue #38): keine toten internen Links.

Geprüft werden href/src in allen HTML-Seiten und url() in den Stylesheets. Ziele mit Schema
(https:, mailto: …) sind extern und hier ausgenommen. Anker (#id) müssen auf der Zielseite
als id existieren.
"""

import html
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

from generator.build import build

ATTRIBUT = re.compile(r"""\b(?:href|src)\s*=\s*["']([^"']*)["']""", re.IGNORECASE)
CSS_URL = re.compile(r"""url\(\s*["']?([^"')]+)["']?\s*\)""")
# Inhalt eingebetteter Skripte ist kein Markup (`link.href = "/static/fonts/" + …` ist kein Link);
# das öffnende Tag bleibt, damit `<script src=…>` weiter geprüft wird.
SKRIPT_INHALT = re.compile(r"(<script\b[^>]*>).*?</script>", re.IGNORECASE | re.DOTALL)
ID = re.compile(r"""\bid\s*=\s*["']([^"']+)["']""")


def ist_intern(ziel: str) -> bool:
    teile = urlsplit(ziel)
    return not (teile.scheme or teile.netloc)


def zieldatei(dist: Path, quelle: Path, pfad: str) -> Path:
    """Datei, die ein Webserver für `pfad` (relativ zu `quelle`) ausliefert."""
    pfad = unquote(pfad)
    basis = dist if pfad.startswith("/") else quelle.parent
    ziel = (basis / pfad.lstrip("/")).resolve()
    return ziel / "index.html" if pfad.endswith("/") or ziel.is_dir() else ziel


def tote_links(dist: Path) -> list[str]:
    ids: dict[Path, set[str]] = {}

    def ids_von(datei: Path) -> set[str]:
        if datei not in ids:
            ids[datei] = set(ID.findall(datei.read_text(encoding="utf-8")))
        return ids[datei]

    befunde = []
    dateien = [*dist.rglob("*.html"), *dist.rglob("*.css")]
    for quelle in sorted(dateien):
        text = quelle.read_text(encoding="utf-8")
        if quelle.suffix == ".css":
            muster = CSS_URL
        else:
            muster = ATTRIBUT
            text = SKRIPT_INHALT.sub(r"\1</script>", text)
        for roh in muster.findall(text):
            ziel = html.unescape(roh)
            if not ziel or not ist_intern(ziel) or ziel.startswith("data:"):
                continue
            teile = urlsplit(ziel)
            datei = zieldatei(dist, quelle, teile.path) if teile.path else quelle.resolve()
            herkunft = quelle.relative_to(dist).as_posix()
            if not datei.is_file():
                befunde.append(f"{herkunft}: {ziel} (Datei fehlt)")
            elif teile.fragment and datei.suffix == ".html":
                if unquote(teile.fragment) not in ids_von(datei):
                    befunde.append(f"{herkunft}: {ziel} (Anker fehlt)")
    return befunde


@pytest.fixture(scope="module")
def dist(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return out


def test_build_hat_keine_toten_internen_links(dist: Path):
    assert tote_links(dist) == []


def test_link_check_findet_fehlende_seiten_dateien_und_anker(tmp_path: Path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "index.html").write_text('<h2 id="da">x</h2>', encoding="utf-8")
    (tmp_path / "s.css").write_text("x{background:url('/fehlt.png')}", encoding="utf-8")
    (tmp_path / "index.html").write_text(
        '<a href="/a/">ok</a> <a href="/a/#da">ok</a> <a href="#oben" id="oben">ok</a>'
        '<a href="https://example.org/x">extern</a> <a href="&#109;ailto:x@y.de">mail</a>'
        '<a href="/b/">tot</a> <a href="/a/#weg">tot</a> <img src="bild.png">',
        encoding="utf-8",
    )
    assert tote_links(tmp_path) == [
        "index.html: /b/ (Datei fehlt)",
        "index.html: /a/#weg (Anker fehlt)",
        "index.html: bild.png (Datei fehlt)",
        "s.css: /fehlt.png (Datei fehlt)",
    ]
