"""Rechte Spalte der Methodenseite (Issue #8): Druckvorlagen, digitale Tools, Passt auch dazu."""

import re
from pathlib import Path

import pytest

from generator.build import build
from generator.content import load_site
from generator.methodenseite import digitale_tools, passt_auch_dazu


@pytest.fixture(scope="module")
def site():
    return load_site()


def methode(site, methoden_id):
    return next(m for m in site.methoden if m.id == methoden_id)


def test_passt_auch_dazu_verwandt_zuerst_dann_gleiche_kategorie(site):
    # kugellager (E) hat nur verwandt [blitzlicht]; aufgefüllt mit E nach Titel (DIN 5007),
    # ohne die Methode selbst und ohne blitzlicht doppelt.
    ids = [m.id for m in passt_auch_dazu(methode(site, "kugellager"), site)]
    assert ids == ["blitzlicht", "briefkasten", "fragebogen"]


def test_passt_auch_dazu_hoechstens_drei_und_verwandt_aus_anderer_kategorie(site):
    # blitzlicht (E): verwandt [5-finger-methode (A), kugellager], dann E nach Titel.
    ids = [m.id for m in passt_auch_dazu(methode(site, "blitzlicht"), site)]
    assert ids == ["5-finger-methode", "kugellager", "briefkasten"]


def test_passt_auch_dazu_kleine_kategorie_liefert_weniger(site):
    # B hat nur drei Methoden: aufstellung bekommt die anderen beiden.
    ids = [m.id for m in passt_auch_dazu(methode(site, "aufstellung"), site)]
    assert ids == ["4-ecken-methode", "fahrstuhlmethode"]


def test_digitale_tools_aus_methode_und_tools_yaml(site):
    # wortwolke: Feld tools [mentimeter, oncoo]; oncoo nennt sie auch selbst – keine Dopplung.
    assert [t.id for t in digitale_tools(methode(site, "wortwolke"), site)] == [
        "mentimeter",
        "oncoo",
    ]
    # 4-ecken-methode ist analog: plickers nennt sie in tools.yaml, zählt aber nicht (PRD §5.3).
    assert digitale_tools(methode(site, "4-ecken-methode"), site) == []
    assert digitale_tools(methode(site, "daumenprobe"), site) == []


@pytest.fixture(scope="module")
def dist(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return out


def seitenleiste(dist: Path, methoden_id: str) -> str:
    html = (dist / "methoden" / methoden_id / "index.html").read_text(encoding="utf-8")
    match = re.search(r'<aside class="methode__seite".*?</aside>', html, flags=re.S)
    assert match, "rechte Spalte fehlt"
    return match.group(0)


def test_methode_mit_druckvorlage_zeigt_download_bereich(dist: Path):
    html = seitenleiste(dist, "exit-ticket")
    assert 'class="seitenleiste__druck"' in html
    assert re.search(
        r'<a class="knopf knopf--haupt" href="/vorlagen/exit-ticket/">\s*Vorlage drucken', html
    )


def test_mehrere_druckvorlagen_werden_alle_verlinkt(dist: Path):
    html = seitenleiste(dist, "klebepunkte")
    assert 'href="/vorlagen/skalen-plakat/"' in html
    assert 'href="/vorlagen/wettersymbole/"' in html
    assert "Druckvorlagen</h2>" in html


def test_methode_ohne_druckvorlage_hat_keinen_download_bereich(dist: Path):
    html = seitenleiste(dist, "daumenprobe")
    assert "seitenleiste__druck" not in html
    assert "/vorlagen/" not in html


def test_platzhalter_vorlage_ist_gekennzeichnet(dist: Path):
    html = seitenleiste(dist, "wimmelbild-zuordnen")
    assert 'href="/vorlagen/wimmelbild/"' in html
    assert '<span class="status-hinweis">Vorlage folgt</span>' in html
    assert "Vorlage drucken" not in html


def test_anleitung_drucken_knopf_immer_vorhanden(dist: Path):
    for methoden_id in ("exit-ticket", "daumenprobe"):
        assert "data-drucken" in seitenleiste(dist, methoden_id)


def test_digitale_methode_verlinkt_ihre_tools(dist: Path):
    html = seitenleiste(dist, "wortwolke")
    assert 'class="seitenleiste__digital"' in html
    assert 'href="https://www.mentimeter.com" rel="noopener noreferrer">Mentimeter' in html
    assert 'href="https://www.oncoo.de" rel="noopener noreferrer">Oncoo' in html
    assert 'href="/tools/"' in html


def test_digitale_methode_ohne_eigene_tools_verweist_auf_toolseite(dist: Path):
    html = seitenleiste(dist, "laermampel")
    assert 'class="seitenleiste__digital"' in html
    assert 'href="/tools/"' in html


def test_analoge_methode_ohne_tools_hat_keinen_digitalbereich(dist: Path):
    assert "seitenleiste__digital" not in seitenleiste(dist, "daumenprobe")


def test_analoge_methode_aus_tools_yaml_hat_keinen_digitalbereich(dist: Path):
    # PRD §5.3: Tool-Links nur bei digitalen Methoden.
    assert "seitenleiste__digital" not in seitenleiste(dist, "4-ecken-methode")


def test_passt_auch_dazu_verlinkt_hoechstens_drei_methoden(dist: Path):
    html = seitenleiste(dist, "blitzlicht")
    links = re.findall(r'<a class="vorschlag" href="(/methoden/[^"]+/)"', html)
    assert links == [
        "/methoden/5-finger-methode/",
        "/methoden/kugellager/",
        "/methoden/briefkasten/",
    ]
