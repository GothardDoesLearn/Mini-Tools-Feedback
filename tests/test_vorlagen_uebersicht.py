"""Vorlagen-Übersicht /vorlagen/ (Issue #21)."""

import re
from pathlib import Path

import pytest

from generator.build import build
from generator.content import load_site


@pytest.fixture(scope="module")
def site():
    return load_site()


@pytest.fixture(scope="module")
def uebersicht(tmp_path_factory) -> str:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return (out / "vorlagen" / "index.html").read_text(encoding="utf-8")


def _eintrag(html: str, vorlagen_id: str) -> str:
    """HTML des Listeneintrags einer Vorlage."""
    m = re.search(rf'<li class="vorlagen__eintrag" id="vorlage-{vorlagen_id}">.*?</li>', html, re.S)
    assert m, vorlagen_id
    return m.group(0)


def test_alle_vorlagen_sind_gelistet_und_verlinkt(uebersicht: str, site):
    assert len(site.druckvorlagen) == 18
    for v in site.druckvorlagen:
        eintrag = _eintrag(uebersicht, v.id)
        assert f'href="/vorlagen/{v.id}/"' in eintrag
        assert v.titel in eintrag


def test_eintrag_verlinkt_zugehoerige_methoden_mit_titel(uebersicht: str, site):
    titel = {m.id: m.titel for m in site.methoden}
    for v in site.druckvorlagen:
        eintrag = _eintrag(uebersicht, v.id)
        for methoden_id in (m.id for m in site.methoden_mit_vorlage(v.id)):
            assert f'href="/methoden/{methoden_id}/"' in eintrag
            assert titel[methoden_id] in eintrag


def test_status_annahme_und_platzhalter_sind_sichtbar_gekennzeichnet(uebersicht: str, site):
    stati = {v.status for v in site.druckvorlagen}
    assert {"annahme", "platzhalter"} <= stati  # sonst testet der Test nichts
    for v in site.druckvorlagen:
        eintrag = _eintrag(uebersicht, v.id)
        if v.status == "fertig":
            assert "status-hinweis" not in eintrag
        elif v.status == "annahme":
            assert '<span class="status-hinweis">wird geprüft</span>' in eintrag
        else:
            assert '<span class="status-hinweis">Vorlage folgt</span>' in eintrag


def test_navigation_druckvorlagen_ist_aktiv(uebersicht: str):
    assert '<a class="hauptnav__link" href="/vorlagen/" aria-current="page">' in uebersicht
    assert "<h1>Druckvorlagen</h1>" in uebersicht


def test_status_hinweis_hat_badge_stil_aus_design_md(tmp_path: Path):
    build(output_dir=tmp_path)
    css = (tmp_path / "static" / "css" / "site.css").read_text(encoding="utf-8")
    regel = re.search(r"\.status-hinweis\s*\{(.*?)\}", css, re.S).group(1)
    assert "#FFF1D6" in regel
    assert "#7A4B00" in regel
