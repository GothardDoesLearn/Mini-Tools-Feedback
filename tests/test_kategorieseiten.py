"""Kategorieseiten /kategorien/<slug>/ (Issue #12)."""

import re
from pathlib import Path

import pytest

from generator.build import build


@pytest.fixture(scope="module")
def dist(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return out


def _karten(html: str) -> list[str]:
    return re.findall(r'<article class="karte".*?</article>', html, re.S)


def test_sieben_kategorieseiten_werden_gebaut(dist: Path):
    seiten = sorted(p.parent.name for p in (dist / "kategorien").glob("*/index.html"))
    assert seiten == sorted(
        [
            "handzeichen-karten",
            "positionieren-im-raum",
            "skalieren-visualisieren",
            "lernstand-pruefen",
            "reflexion-gespraech",
            "peer-feedback",
            "klassenklima",
        ]
    )


def test_kategorieseite_zeigt_titel_beschreibung_und_ihre_methoden(dist: Path):
    html = (dist / "kategorien/handzeichen-karten/index.html").read_text(encoding="utf-8")
    assert "<h1>Handzeichen &amp; Karten</h1>" in html
    assert "Alle SuS antworten gleichzeitig vom Platz aus" in html
    assert "<title>Handzeichen &amp; Karten – " in html
    karten = _karten(html)
    assert karten and all(">Handzeichen</" in k for k in karten)
    assert any('href="/methoden/ampel/"' in k for k in karten)


def test_jede_methode_steht_auf_genau_einer_kategorieseite(dist: Path):
    ids = []
    for seite in (dist / "kategorien").glob("*/index.html"):
        html = seite.read_text(encoding="utf-8")
        ids += re.findall(r'href="/methoden/([a-z0-9-]+)/"', "".join(_karten(html)))
    assert sorted(ids) == sorted(p.stem for p in Path("content/methoden").glob("*.md"))


def test_kategorie_auf_karten_der_startseite_verlinkt_die_kategorieseite(dist: Path):
    karten = _karten((dist / "index.html").read_text(encoding="utf-8"))
    links = [re.search(r'class="karte__kategorie[^"]*"[^>]*href="([^"]+)"', k) for k in karten]
    assert all(links)
    for link in {m.group(1) for m in links}:
        assert link.startswith("/kategorien/")
        assert (dist / link.strip("/") / "index.html").is_file(), link
