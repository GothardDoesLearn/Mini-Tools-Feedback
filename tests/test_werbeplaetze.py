"""Werbeplätze: vorbereitet, per Konfiguration ausgeschaltet (Issue #36, ADR 0001)."""

import re
from pathlib import Path

import pytest

from generator.build import build
from generator.config import load_config
from generator.css import stylesheet

WERBEPLATZ = re.compile(r'<div class="werbeplatz[^"]*"[^>]*></div>')


def _bauen(tmp_path_factory, **einstellungen) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out, config=load_config().model_copy(update=einstellungen))
    return out


@pytest.fixture(scope="module")
def aus(tmp_path_factory) -> Path:
    return _bauen(tmp_path_factory, werbung_aktiv=False)


@pytest.fixture(scope="module")
def an(tmp_path_factory) -> Path:
    return _bauen(tmp_path_factory, werbung_aktiv=True, werbung_nach_karten=6)


def _seiten(dist: Path) -> list[Path]:
    return sorted(dist.rglob("*.html"))


def test_ausgeschaltet_erzeugt_kein_zusaetzliches_html(aus: Path):
    for seite in _seiten(aus):
        assert "werbeplatz" not in seite.read_text(encoding="utf-8"), seite


def test_methodenseite_hat_eingeschaltet_einen_platz_unter_der_anleitung(an: Path):
    seiten = sorted((an / "methoden").glob("*/index.html"))
    assert len(seiten) == 31
    for seite in seiten:
        html = seite.read_text(encoding="utf-8")
        plaetze = WERBEPLATZ.findall(html)
        assert len(plaetze) == 1, seite
        haupt = html.split('<div class="methode__haupt anleitung">', 1)[1]
        haupt = haupt.split('<aside class="methode__seite"', 1)[0]
        # nach dem letzten Anleitungsabschnitt, aber noch in der Hauptspalte
        assert haupt.rfind("werbeplatz") > haupt.rfind("</section>"), seite


def test_uebersicht_hat_nach_jeder_n_ten_karte_einen_platz(an: Path):
    html = (an / "index.html").read_text(encoding="utf-8")
    raster = html.split('<div class="karten">', 1)[1].split("</section>", 1)[0]
    folge = re.findall(r'<article class="karte"|<div class="werbeplatz', raster)
    karten_vor_platz = [
        folge[:i].count('<article class="karte"')
        for i, eintrag in enumerate(folge)
        if eintrag.startswith("<div")
    ]
    # 31 Karten, n = 6: nach Karte 6, 12, 18, 24, 30 – nicht hinter der letzten Karte
    assert karten_vor_platz == [6, 12, 18, 24, 30]


def test_abstand_n_kommt_aus_der_konfiguration(tmp_path_factory):
    out = _bauen(tmp_path_factory, werbung_aktiv=True, werbung_nach_karten=10)
    html = (out / "index.html").read_text(encoding="utf-8")
    assert len(WERBEPLATZ.findall(html)) == 3


def test_konfiguration_legt_n_fest_und_ist_mindestens_1(tmp_path: Path):
    from pydantic import ValidationError

    assert load_config().werbung_nach_karten >= 1
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        'website_name: "X"\ndomain: "https://x.example"\nbeschreibung: "X"\n'
        "werbung_nach_karten: 0\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_config(config_file)


def test_nie_auf_druckvorlagen(an: Path):
    seiten = _seiten(an / "vorlagen")
    assert seiten
    for seite in seiten:
        assert "werbeplatz" not in seite.read_text(encoding="utf-8"), seite


def _css_ohne_kommentare() -> str:
    text = stylesheet("site")
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def test_druckansicht_blendet_werbeplaetze_aus():
    druck = _css_ohne_kommentare().split("@media print", 1)[1]
    regeln = re.findall(r"([^{}]*)\{([^{}]*)\}", druck.split("{", 1)[1])
    assert any(".werbeplatz" in sel and "display: none" in dekl for sel, dekl in regeln)


def test_werbeplatz_im_kartenraster_ueberspannt_die_ganze_zeile():
    regel = re.search(r"\.werbeplatz--uebersicht\s*\{([^{}]*)\}", _css_ohne_kommentare())
    assert regel and "grid-column: 1 / -1" in regel.group(1)


def test_eingeschaltet_keine_anfragen_an_drittserver(an: Path):
    for seite in _seiten(an):
        for platz in WERBEPLATZ.findall(seite.read_text(encoding="utf-8")):
            assert "//" not in platz and "<script" not in platz
    assert not list(an.rglob("*.js")) or all(
        "werbe" not in p.read_text(encoding="utf-8") for p in an.rglob("*.js")
    )
