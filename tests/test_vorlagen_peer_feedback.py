"""Druckvorlagen aus Issue #28: sterne-wunsch-karte, www-karte, burger, beobachtungsbogen."""

from pathlib import Path

import pytest

from generator.build import build
from generator.content import load_site


@pytest.fixture(scope="module")
def dist(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return out


def seite(dist: Path, vorlagen_id: str) -> str:
    return (dist / "vorlagen" / vorlagen_id / "index.html").read_text(encoding="utf-8")


def blaetter(html: str) -> list[str]:
    return html.split('<section class="blatt')[1:]


@pytest.mark.parametrize(
    "vorlagen_id", ["sterne-wunsch-karte", "www-karte", "burger", "beobachtungsbogen"]
)
def test_seitenzahl_wie_spezifiziert_ohne_werbung(dist: Path, vorlagen_id: str):
    vorlage = next(v for v in load_site().druckvorlagen if v.id == vorlagen_id)
    html = seite(dist, vorlagen_id)

    assert "Vorlage folgt" not in html
    assert len(blaetter(html)) == int(vorlage.seiten)
    assert "werbeplatz" not in "".join(blaetter(html))
    assert "<img" not in html


def test_sterne_wunsch_karte_vier_karten_mit_zwei_sternen_und_wunsch(dist: Path):
    (blatt,) = blaetter(seite(dist, "sterne-wunsch-karte"))

    assert blatt.count('class="druckkarte"') == 4
    assert blatt.count("Feedback für:") == 4
    assert blatt.count('class="symbol symbol--stern"') == 8
    assert blatt.count("</svg>Wunsch</p>") == 4


def test_www_karte_vier_karten_und_plakat_mit_satzanfaengen(dist: Path):
    karten, plakat = blaetter(seite(dist, "www-karte"))

    assert karten.count('class="druckkarte"') == 4
    for text in (
        "Wahrnehmung",
        "Ich habe gesehen/gehört, dass …",
        "Wirkung",
        "Das hat auf mich … gewirkt.",
        "Wunsch",
        "Ich wünsche mir / Mein Tipp …",
    ):
        assert karten.count(text) == 4
        assert plakat.count(text) == 1
    assert "plakat" in plakat


def test_burger_drei_ebenen_lob_tipp_lob(dist: Path):
    (blatt,) = blaetter(seite(dist, "burger"))

    ebenen = blatt.split('class="burger__ebene')[1:]
    assert len(ebenen) == 3
    assert [e.split('class="feld__beschriftung">')[1].split("<")[0] for e in ebenen] == [
        "Lob",
        "Tipp",
        "Lob",
    ]
    for ebene in ebenen:
        assert "feld__linie" in ebene


def test_beobachtungsbogen_kriterien_strichliste_notizfeld(dist: Path):
    (blatt,) = blaetter(seite(dist, "beobachtungsbogen"))

    for kriterium in (
        "alle kommen zu Wort",
        "bleiben beim Thema",
        "hören einander zu",
        "teilen Aufgaben auf",
    ):
        assert f"<td>{kriterium}</td>" in blatt
    assert blatt.count("<tr>") == 1 + 6  # Kopfzeile + 4 Kriterien + 2 leere
    assert blatt.count('<td class="bogen__leer">') == 2
    assert "Strichliste" in blatt
    assert "Notizen" in blatt
