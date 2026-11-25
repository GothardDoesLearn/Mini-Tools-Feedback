"""Issue #35: eigene 404, Seitentitel und Description je Seite, Favicon-Platzhalter."""

import re
from pathlib import Path

import pytest

from generator.build import build, kurzbeschreibung


@pytest.fixture(scope="module")
def dist(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return out


def _seiten(dist: Path) -> list[Path]:
    return sorted(dist.rglob("*.html"))


def _title(html: str) -> str:
    return re.search(r"<title>(.*?)</title>", html, re.S).group(1).strip()


def _description(html: str) -> str:
    return re.search(r'<meta name="description" content="([^"]*)">', html).group(1)


def test_404_seite_wird_als_404_html_im_wurzelverzeichnis_ausgegeben(dist: Path):
    html = (dist / "404.html").read_text(encoding="utf-8")
    assert "<h1>Seite nicht gefunden</h1>" in html
    assert 'href="/"' in html
    assert '<meta name="robots" content="noindex">' in html
    assert _title(html) == "Seite nicht gefunden – Feedback-Tools"


def test_jede_seite_hat_eindeutigen_titel_und_description(dist: Path):
    seiten = _seiten(dist)
    assert len(seiten) >= 2
    titel = [_title(p.read_text(encoding="utf-8")) for p in seiten]
    beschreibungen = [_description(p.read_text(encoding="utf-8")) for p in seiten]
    assert all(titel) and all(beschreibungen)
    assert len(set(titel)) == len(titel), titel
    assert len(set(beschreibungen)) == len(beschreibungen), beschreibungen


def test_jede_seite_bindet_lokales_favicon_ein(dist: Path):
    for seite in _seiten(dist):
        html = seite.read_text(encoding="utf-8")
        assert '<link rel="icon" href="/static/favicon.svg" type="image/svg+xml">' in html, seite
    svg = (dist / "static" / "favicon.svg").read_text(encoding="utf-8")
    assert svg.lstrip().startswith("<svg")


def test_kurzbeschreibung_entfernt_markdown_und_kuerzt_an_wortgrenze():
    text = "Die **SuS** zeigen mit dem [Daumen](https://x.y), wie es war.\n\nZweiter Absatz."
    assert kurzbeschreibung(text) == "Die SuS zeigen mit dem Daumen, wie es war. Zweiter Absatz."
    lang = "wort " * 60
    gekuerzt = kurzbeschreibung(lang, max_laenge=30)
    assert gekuerzt == "wort wort wort wort wort wort…"
