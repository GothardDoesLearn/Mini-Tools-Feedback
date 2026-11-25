"""Startseite: Intro und Kategorie-Auswahl, noch ohne Filterfunktion (Issue #11)."""

import re
from pathlib import Path

import pytest

from generator.build import build
from generator.content import ContentError, load_site, load_startseite
from generator.startseite import kategorie_auswahl


@pytest.fixture(scope="module")
def startseite(tmp_path_factory) -> str:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return (out / "index.html").read_text(encoding="utf-8")


def test_kategorie_auswahl_beginnt_mit_alle_und_zaehlt_methoden_je_kategorie():
    eintraege = kategorie_auswahl(load_site())

    assert [e.kurzname for e in eintraege] == [
        "Alle",
        "Handzeichen",
        "Im Raum",
        "Skalieren",
        "Lernstand",
        "Reflexion",
        "Peer-Feedback",
        "Klassenklima",
    ]
    assert eintraege[0].id == "" and eintraege[0].anzahl == 31
    assert eintraege[1].id == "A" and eintraege[1].anzahl == 6
    assert sum(e.anzahl for e in eintraege[1:]) == 31


def test_intro_kommt_aus_content_startseite_yaml(startseite: str):
    texte = load_startseite()

    assert texte.titel and texte.intro
    assert f'<h1 class="intro__titel">{texte.titel}</h1>' in startseite
    assert f'<p class="intro__text">{texte.intro}</p>' in startseite


def _kategorie_buttons(html: str) -> list[str]:
    gruppe = re.search(r'<div class="kategorie-auswahl__liste" role="group".*?</div>', html, re.S)
    assert gruppe, "Kategorie-Gruppe fehlt"
    return re.findall(r"<button.*?</button>", gruppe.group(0), re.S)


def test_kategorie_auswahl_zeigt_alle_und_sieben_kategorien_als_buttons(startseite: str):
    buttons = _kategorie_buttons(startseite)

    assert len(buttons) == 8
    assert all('type="button"' in b for b in buttons)
    assert 'aria-pressed="true"' in buttons[0] and 'data-kategorie=""' in buttons[0]
    assert ">Alle<" in buttons[0] and "31 Methoden" in buttons[0]
    assert all('aria-pressed="false"' in b for b in buttons[1:])
    handzeichen = buttons[1]
    assert 'data-kategorie="A"' in handzeichen
    assert ">Handzeichen<" in handzeichen and "6 Methoden" in handzeichen
    assert "--kategorie-papier: #FFF6C7" in handzeichen
    assert "--kategorie-pin: #D62F2F" in handzeichen
    assert "--kategorie-farbe: #2E7D32" in handzeichen


def test_kategorie_auswahl_steht_in_der_filterspalte_vor_den_karten(startseite: str):
    spalte = startseite.index('<aside class="filterspalte"')
    assert (
        spalte < startseite.index("kategorie-auswahl__liste") < startseite.index('class="karten"')
    )


@pytest.fixture(scope="module")
def css() -> str:
    text = Path("static/css/site.css").read_text(encoding="utf-8")
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def _regel(css: str, selektor: str) -> str:
    treffer = re.search(rf"(?:^|\}}|,)\s*{re.escape(selektor)}\s*\{{([^{{}}]*)\}}", css)
    assert treffer, selektor
    return treffer.group(1)


def _pinnwand(css: str) -> str:
    return css[css.index("@media screen {") : css.index("@media screen and (prefers-reduced")]


def test_kategorie_liste_ist_auf_schmalen_bildschirmen_seitlich_wischbar(css: str):
    liste = _regel(css, ".kategorie-auswahl__liste")
    assert "overflow-x: auto" in liste and "flex-wrap: nowrap" in liste
    assert "flex-wrap: nowrap" in _regel(
        _pinnwand(css), '[data-ansicht="pinnwand"] .kategorie-auswahl__liste'
    )


def test_klare_liste_mit_farbpunkt_und_hellblauer_auswahl(css: str):
    assert "var(--kategorie-farbe)" in _regel(css, ".kategorie-auswahl__eintrag::before")
    eintrag = _regel(css, ".kategorie-auswahl__eintrag")
    assert "min-height: var(--ziel-min)" in eintrag
    gewaehlt = _regel(css, '.kategorie-auswahl__eintrag[aria-pressed="true"]')
    assert "font-weight: 700" in gewaehlt and "background: #E8F0FC" in gewaehlt


def test_pinnwand_ovale_mit_pin_und_angehobener_auswahl(css: str):
    pinnwand = _pinnwand(css)
    oval = _regel(pinnwand, '[data-ansicht="pinnwand"] .kategorie-auswahl__eintrag')
    assert "flex: 0 0 132px" in oval and "height: 84px" in oval
    assert "border-radius: 50%" in oval and "var(--kategorie-papier)" in oval
    assert "rotate(" in oval
    pin = _regel(pinnwand, '[data-ansicht="pinnwand"] .kategorie-auswahl__eintrag::before')
    assert "var(--kategorie-pin)" in pin
    gewaehlt = _regel(
        pinnwand, '[data-ansicht="pinnwand"] .kategorie-auswahl__eintrag[aria-pressed="true"]'
    )
    assert "translateY(-6px) scale(1.07)" in gewaehlt and "outline: 3px solid" in gewaehlt


def test_pinnwand_zusatztext_der_ueberschrift_nur_in_der_pinnwand(css: str):
    assert "display: none" in _regel(css, ".nur-filz")
    assert "display: inline" in _regel(_pinnwand(css), '[data-ansicht="pinnwand"] .nur-filz')


def test_startseite_yaml_ohne_intro_bricht_mit_klarer_meldung_ab(tmp_path: Path):
    (tmp_path / "startseite.yaml").write_text('titel: "X"\n', encoding="utf-8")

    with pytest.raises(ContentError, match=r"(?s)startseite\.yaml:.*intro"):
        load_startseite(tmp_path)
