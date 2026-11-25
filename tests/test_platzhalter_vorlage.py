"""Issue #29: Platzhalter-Vorlage Wimmelbild – „Vorlage folgt“, zählt nicht als Druckvorlage."""

import re
from pathlib import Path

import pytest

from generator.build import build
from generator.content import load_site
from generator.karten import karten


@pytest.fixture(scope="module")
def dist(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return out


def _karte(html: str, methoden_id: str) -> str:
    treffer = re.search(
        rf'<article class="karte" data-methode="{methoden_id}".*?</article>', html, re.S
    )
    assert treffer, methoden_id
    return treffer.group(0)


def test_platzhalter_seite_vorlage_folgt_baut(dist: Path):
    html = (dist / "vorlagen" / "wimmelbild" / "index.html").read_text(encoding="utf-8")
    assert "Vorlage folgt" in html
    assert '<section class="blatt' not in html
    assert "<img" not in html  # kein fremdes Bild


def test_karte_zeigt_kein_druckvorlagen_icon_fuer_platzhalter_vorlage():
    karte = next(k for k in karten(load_site()) if k.id == "wimmelbild-zuordnen")
    assert karte.druckvorlage is False
    assert karte.filterwerte["druckvorlage"] == ["nein"]


def test_karte_und_filter_sind_bei_druckvorlage_konsistent():
    for k in karten(load_site()):
        assert k.druckvorlage == (k.filterwerte["druckvorlage"] == ["ja"]), k.id


def test_startseite_wimmelbild_ohne_druckvorlage_bei_filter_ja(dist: Path):
    karte = _karte((dist / "index.html").read_text(encoding="utf-8"), "wimmelbild-zuordnen")
    assert 'data-filter-druckvorlage="nein"' in karte
    assert "karte__info--druckvorlage" not in karte


def test_methodenseite_ohne_druckknopf_fuer_platzhalter_vorlage(dist: Path):
    html = (dist / "methoden" / "wimmelbild-zuordnen" / "index.html").read_text(encoding="utf-8")
    assert "Vorlage drucken" not in html
    assert 'href="/vorlagen/wimmelbild/"' in html
