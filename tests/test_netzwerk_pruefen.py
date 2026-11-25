"""Reine Teile von tools/netzwerk_pruefen.py (ohne Browser)."""

from pathlib import Path

import pytest

from tools.druck_pruefen import Fehler
from tools.netzwerk_pruefen import (
    MESSSKRIPT,
    fremde_urls,
    gemessene_urls,
    messskript_einfuegen,
    seitenpfade,
)


def test_messskript_steht_direkt_hinter_head():
    html = b'<!doctype html><html><head lang="de"><script src="/a.js"></script></head>'
    ergebnis = messskript_einfuegen(html)
    assert ergebnis.startswith(b'<!doctype html><html><head lang="de">' + MESSSKRIPT.encode())
    assert ergebnis.endswith(b'<script src="/a.js"></script></head>')


def test_gemessene_urls_aus_dem_dom():
    dom = '<body><pre id="__netzwerk">["http://127.0.0.1:1/a.css","https://x.de/&amp;"]</pre>'
    assert gemessene_urls(dom) == ["http://127.0.0.1:1/a.css", "https://x.de/&"]


def test_fehlende_liste_ist_ein_fehler():
    with pytest.raises(Fehler):
        gemessene_urls("<body></body>")


def test_fremde_urls_vergleichen_schema_host_und_port():
    basis = "http://127.0.0.1:8000"
    urls = [
        "http://127.0.0.1:8000/static/a.css",
        "http://127.0.0.1:9000/b.css",
        "https://127.0.0.1:8000/c.css",
        "https://fonts.example/d.woff2",
    ]
    assert fremde_urls(urls, basis) == urls[1:]


def test_seitenpfade_aus_dem_build(tmp_path: Path):
    for datei in ("index.html", "404.html", "methoden/a/index.html", "static/x.css"):
        (tmp_path / datei).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / datei).write_text("", encoding="utf-8")
    assert seitenpfade(tmp_path) == ["/404.html", "/", "/methoden/a/"]
