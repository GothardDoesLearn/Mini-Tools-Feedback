"""Druckvorlagen aus Issue #23: smiley-karten, ampelkarten, feedback-hand."""

from pathlib import Path

import pytest

from generator.build import build


@pytest.fixture(scope="module")
def dist(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return out


def seite(dist: Path, vorlagen_id: str) -> str:
    return (dist / "vorlagen" / vorlagen_id / "index.html").read_text(encoding="utf-8")


def blaetter(html: str) -> list[str]:
    return html.split('<section class="blatt')[1:]


def test_smiley_karten_ein_blatt_mit_vier_karten_je_drei_smileys(dist: Path):
    html = seite(dist, "smiley-karten")

    (blatt,) = blaetter(html)
    assert "Vorlage folgt" not in html
    assert blatt.count('class="smiley-karte"') == 4
    for gesicht in ("lachend", "neutral", "traurig"):
        assert blatt.count(f'data-smiley="{gesicht}"') == 4


def test_ampelkarten_drei_blaetter_je_farbe_mit_vier_a7_karten_und_sw_text(dist: Path):
    html = seite(dist, "ampelkarten")

    rot, gelb, gruen = blaetter(html)
    for blatt, farbe, text in (
        (rot, "rot", "Hilfe"),
        (gelb, "gelb", "unsicher"),
        (gruen, "gruen", "verstanden"),
    ):
        assert blatt.count(f'class="ampel-karte ampel-karte--{farbe}"') == 4
        assert blatt.count(f'<p class="ampel-karte__text">{text}</p>') == 4


def test_feedback_hand_ein_blatt_mit_hand_und_fuenf_leitsaetzen_mit_schreibfeld(dist: Path):
    html = seite(dist, "feedback-hand")

    (blatt,) = blaetter(html)
    assert 'class="hand"' in blatt
    for finger, leitsatz in (
        ("Daumen", "Das war super"),
        ("Zeigefinger", "Das ist mir aufgefallen"),
        ("Mittelfinger", "Das hat mir nicht gefallen"),
        ("Ringfinger", "Das nehme ich mit"),
        ("kleiner Finger", "Das kam zu kurz"),
    ):
        assert f"{finger}: {leitsatz}" in blatt
    assert blatt.count('class="hand-feld"') == 5
    assert blatt.count('class="feld__linie"') >= 10
