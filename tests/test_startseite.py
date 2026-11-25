"""Methodenkarte und Startseite mit allen Methoden (Issue #10)."""

import re
from pathlib import Path

import pytest

from generator.build import build
from generator.content import Methode, load_site
from generator.karten import kurztext


@pytest.fixture(scope="module")
def startseite(tmp_path_factory) -> str:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return (out / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def css() -> str:
    text = Path("static/css/site.css").read_text(encoding="utf-8")
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def _regel(css: str, selektor: str) -> str:
    treffer = re.search(rf"(?:^|\}}|,)\s*{re.escape(selektor)}\s*\{{([^{{}}]*)\}}", css)
    assert treffer, selektor
    return treffer.group(1)


def _karten(html: str) -> list[str]:
    return re.findall(r'<article class="karte".*?</article>', html, re.S)


def _karte(html: str, methoden_id: str) -> str:
    treffer = [k for k in _karten(html) if f'href="/methoden/{methoden_id}/"' in k]
    assert len(treffer) == 1, methoden_id
    return treffer[0]


def test_kategorien_haben_kurzname_papier_und_pin_aus_design_md():
    a = load_site().kategorien[0]
    assert (a.kurzname, a.papier, a.pin) == ("Handzeichen", "#FFF6C7", "#D62F2F")


def test_startseite_zeigt_31_karten_mit_link_auf_die_methodenseite(startseite: str):
    karten = _karten(startseite)
    assert len(karten) == 31
    ids = [re.search(r'href="/methoden/([a-z0-9-]+)/"', k).group(1) for k in karten]
    assert sorted(ids) == sorted(p.stem for p in Path("content/methoden").glob("*.md"))


def test_karten_sind_nach_kategorie_und_dann_titel_sortiert(startseite: str):
    titel = [
        re.search(r'<a class="karte__link"[^>]*>([^<]+)</a>', k).group(1)
        for k in _karten(startseite)
    ]
    # Kategorie A (Handzeichen) alphabetisch, danach beginnt B mit der 4-Ecken-Methode
    assert titel[:8] == [
        "5-Finger-Methode",
        "Ampel",
        "Daumenprobe",
        "Mini-Whiteboards",
        "Smileys",
        "Wetterbericht",
        "4-Ecken-Methode",
        "Aufstellung",
    ]
    assert titel[-1] == "Lärmampel"


def test_status_badge_nur_bei_annahme_und_platzhalter(startseite: str):
    assert "wird geprüft" in _karte(startseite, "fahrstuhlmethode")
    assert "Platzhalter" in _karte(startseite, "wimmelbild-zuordnen")
    assert "karte__status" not in _karte(startseite, "daumenprobe")
    assert len(re.findall(r'class="karte__status', startseite)) == 3


def test_karte_zeigt_kategorie_dauer_form_und_druckvorlage(startseite: str):
    exit_ticket = _karte(startseite, "exit-ticket")
    assert ">Lernstand<" in exit_ticket
    assert "3–5 Min" in exit_ticket
    assert ">Analog<" in exit_ticket and ">Digital<" in exit_ticket
    assert "karte__info--druckvorlage" in exit_ticket
    assert "--karte-papier: #FADBD8" in exit_ticket and "--karte-pin: #2E8B57" in exit_ticket

    daumenprobe = _karte(startseite, "daumenprobe")
    assert ">Digital<" not in daumenprobe
    assert "karte__info--druckvorlage" not in daumenprobe
    assert "Druckvorlage (optional)" in _karte(startseite, "aufstellung")


def test_icons_sind_fuer_screenreader_ausgeblendet(startseite: str):
    svgs = re.findall(r"<svg[^>]*>", startseite)
    assert svgs and all('aria-hidden="true"' in s for s in svgs)


def test_klare_karte_ist_weiss_mit_rahmen_und_farbpunkt(css: str):
    karte = _regel(css, ".karte")
    assert "var(--farbe-flaeche)" in karte and "var(--farbe-rahmen)" in karte
    assert "var(--karte-farbe)" in _regel(css, ".karte__kategorie::before")


def test_pinnwand_karte_ist_papier_mit_pin_und_gedreht(css: str):
    pinnwand = css[css.index("@media screen {") :]
    karte = _regel(pinnwand, '[data-ansicht="pinnwand"] .karte')
    assert "var(--karte-papier)" in karte and "rotate(" in karte
    assert "var(--karte-pin)" in _regel(pinnwand, '[data-ansicht="pinnwand"] .karte::before')


def test_karten_drehung_entfaellt_bei_reduzierter_bewegung(css: str):
    start = css.index("@media screen and (prefers-reduced-motion: reduce)")
    reduziert = css[start : css.index("@media print")]
    assert '[data-ansicht="pinnwand"] *' in reduziert
    assert "transform: none !important" in reduziert


def test_ganze_karte_ist_klickbar_und_fokus_sichtbar(css: str):
    assert "inset: 0" in _regel(css, ".karte__link::after")
    assert "outline" in _regel(css, ".karte:focus-within")


def _methode(**felder) -> Methode:
    basis = dict(
        id="x",
        titel="X",
        kategorie="A",
        richtung=["peer"],
        zeitpunkt=["einstieg"],
        form=["analog"],
        dauer="1 Min",
        dauer_min=1,
        dauer_max=1,
        material="-",
        druckvorlagen=[],
        status="fertig",
    )
    return Methode(**(basis | felder))


def test_kurztext_ist_feld_kurz_oder_gekuerzter_erster_ablaufschritt():
    lang = "Ein **sehr** langer Schritt " + "mit vielen Wörtern " * 10
    body = f"## Ablauf\n\n1. {lang}\n2. Zweiter Schritt."
    assert kurztext(_methode(kurz="Ein Satz.", body=body)) == "Ein Satz."
    gekuerzt = kurztext(_methode(body=body))
    assert gekuerzt.startswith("Ein sehr langer Schritt mit vielen")
    assert gekuerzt.endswith(" …") and len(gekuerzt) <= 112
    kurz_body = "## Ablauf\n\n1. Alle stehen auf.\n2. Weiter."
    assert kurztext(_methode(body=kurz_body)) == "Alle stehen auf."
