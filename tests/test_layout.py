"""Basis-Layout (Issue #4): Kopf, Navigation, Fuß, klare Ansicht, lokale Schrift, Druck."""

import re
from pathlib import Path

import pytest

from generator.build import build


@pytest.fixture(scope="module")
def dist(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return out


@pytest.fixture(scope="module")
def startseite(dist: Path) -> str:
    return (dist / "index.html").read_text(encoding="utf-8")


def test_seite_hat_semantische_landmarks(startseite: str):
    for tag in ("<header", "<nav", "<main", "<footer"):
        assert tag in startseite, tag
    assert 'aria-label="Hauptnavigation"' in startseite


def test_hauptnavigation_verlinkt_alle_bereiche(startseite: str):
    nav = re.search(r'<nav [^>]*aria-label="Hauptnavigation".*?</nav>', startseite, re.S).group(0)
    links = re.findall(r'<a [^>]*href="([^"]+)"[^>]*>\s*([^<]+?)\s*</a>', nav)
    assert links == [
        ("/", "Methoden"),
        ("/vorlagen/", "Druckvorlagen"),
        ("/tools/", "Digitale Tools"),
        ("/ueber/", "Über"),
    ]


@pytest.fixture(scope="module")
def css(dist: Path) -> str:
    return (dist / "static" / "css" / "site.css").read_text(encoding="utf-8")


def test_seite_bindet_stylesheet_ein(startseite: str, css: str):
    # Startansicht (Pinnwand, gespeicherte Wahl) prüft tests/test_ansicht_umschalter.py.
    assert '<link rel="stylesheet" href="/static/css/site.css">' in startseite


def test_klare_ansicht_definiert_tokens_aus_design_md(css: str):
    block = re.search(r'\[data-ansicht="klar"\]\s*\{(.*?)\}', css, re.S).group(1)
    erwartet = {
        "--farbe-hintergrund": "#F6F7F9",
        "--farbe-flaeche": "#FFFFFF",
        "--farbe-rahmen": "#E3E6EA",
        "--farbe-text": "#1B1F24",
        "--farbe-nebentext": "#4A525C",
        "--farbe-akzent": "#1F5FBF",
    }
    for name, wert in erwartet.items():
        assert re.search(rf"{name}:\s*{wert};", block, re.I), name


def test_inter_wird_lokal_als_woff2_geladen(dist: Path, css: str):
    quellen = re.findall(r'url\("?(/static/fonts/[^")]+)"?\)', css)
    for gewicht in ("400", "500", "600", "700"):
        assert any(gewicht in q and q.endswith(".woff2") for q in quellen), gewicht
    for quelle in quellen:
        assert (dist / quelle.lstrip("/")).is_file(), quelle
    assert re.search(r'font-family:\s*"Inter"', css)


def _media_block(css: str, query: str) -> str:
    start = css.index("{", css.index(f"@media {query}"))
    tiefe = 0
    for i in range(start, len(css)):
        tiefe += {"{": 1, "}": -1}.get(css[i], 0)
        if tiefe == 0:
            return css[start : i + 1]
    raise AssertionError(f"@media {query} nicht geschlossen")


def test_druck_blendet_kopf_navigation_und_fuss_aus(css: str):
    druck = _media_block(css, "print")
    regel = re.search(r"([^{}]+)\{\s*display:\s*none", druck).group(1)
    selektoren = {s.strip() for s in regel.split(",")}
    assert {".kopf", "nav", ".fuss"} <= selektoren


def test_fokus_ist_sichtbar_und_touch_ziele_mindestens_44px(css: str):
    assert re.search(r":focus-visible\s*\{[^}]*outline:\s*var\(--fokus-breite\) solid", css)
    assert "--ziel-min: 44px" in css
    for klasse in (".hauptnav__link", ".logo", ".skiplink"):
        regel = re.search(rf"{re.escape(klasse)}\s*\{{([^}}]*)\}}", css).group(1)
        assert "min-height: var(--ziel-min)" in regel, klasse
