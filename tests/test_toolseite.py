"""Toolseite /tools/ (Issue #13): Karten aus tools.yaml, externe Links, allgemeiner Hinweis."""

import re
from pathlib import Path

import pytest

from generator.build import build
from generator.content import load_site


@pytest.fixture(scope="module")
def dist(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return out


@pytest.fixture(scope="module")
def toolseite(dist: Path) -> str:
    pfad = dist / "tools" / "index.html"
    assert pfad.exists()
    return pfad.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def tools():
    return load_site().tools


def _karte(html: str, tool_id: str) -> str:
    treffer = re.search(rf'<article [^>]*id="tool-{tool_id}".*?</article>', html, re.S)
    assert treffer, tool_id
    return treffer.group(0)


def test_alle_tools_erscheinen_mit_ihren_angaben(toolseite: str, tools):
    assert len(tools) == 5
    for tool in tools:
        karte = _karte(toolseite, tool.id)
        assert tool.titel in karte
        assert tool.zweck in karte
        assert tool.ablauf in karte
        assert tool.sus_geraete in karte
        if tool.hinweis:
            assert tool.hinweis in karte


def test_externe_links_sind_erkennbar(toolseite: str, tools):
    for tool in tools:
        karte = _karte(toolseite, tool.id)
        link = re.search(rf'<a [^>]*href="{re.escape(tool.url)}"[^>]*>.*?</a>', karte, re.S)
        assert link, tool.url
        tag = link.group(0)
        assert 'class="extern-link"' in tag
        assert 'rel="noopener noreferrer"' in tag
        assert "externer Link" in tag  # Hinweis für Screenreader


def test_passende_methoden_sind_verlinkt(toolseite: str, tools):
    methoden = {m.id: m for m in load_site().methoden}
    for tool in tools:
        karte = _karte(toolseite, tool.id)
        for methoden_id in tool.methoden:
            assert f'href="/methoden/{methoden_id}/"' in karte
            assert methoden[methoden_id].titel in karte


def test_allgemeiner_freigabe_hinweis(toolseite: str):
    assert "Bitte prüfen Sie, ob das Tool an Ihrer Schule freigegeben ist." in toolseite


def test_navigation_digitale_tools_ist_aktiv(toolseite: str):
    assert re.search(r'<a [^>]*href="/tools/"[^>]*aria-current="page"', toolseite)
    assert "<h1>Digitale Tools</h1>" in toolseite


def test_externer_link_hat_sichtbare_kennzeichnung_im_css(dist: Path):
    css = (dist / "static" / "css" / "site.css").read_text(encoding="utf-8")
    assert ".extern-link::after" in css
