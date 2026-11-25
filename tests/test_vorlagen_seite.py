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


def seite(dist: Path, vorlagen_id: str) -> str:
    return (dist / "vorlagen" / vorlagen_id / "index.html").read_text(encoding="utf-8")


def test_jede_druckvorlage_hat_eine_eigene_seite(dist: Path):
    for vorlage in load_site().druckvorlagen:
        html = seite(dist, vorlage.id)
        assert f"<h1>{vorlage.titel}</h1>" in html


def blaetter(html: str) -> list[str]:
    return html.split('<section class="blatt')[1:]


def test_exit_ticket_hat_zwei_blaetter_mit_je_vier_tickets(dist: Path):
    html = seite(dist, "exit-ticket")

    standard, variante = blaetter(html)
    assert standard.count('class="ticket"') == 4
    assert variante.count('class="ticket"') == 4
    for text in ("Name (optional)", "Datum", "Das habe ich gelernt", "Das ist mir unklar"):
        assert standard.count(text) == 4
    assert standard.count("Kontrollaufgabe") == 4
    for text in ("3-2-1", "3 Dinge gelernt", "2 interessant", "1 Frage"):
        assert variante.count(text) >= 4


def test_drucken_button_braucht_javascript_sonst_hinweis_auf_strg_p(dist: Path):
    html = seite(dist, "exit-ticket")

    assert '<button type="button" class="knopf" data-drucken hidden>Drucken</button>' in html
    assert "<kbd>Strg</kbd>+<kbd>P</kbd>" in html
    assert '<script src="/static/js/drucken.js" defer></script>' in html
    js = (dist / "static" / "js" / "drucken.js").read_text(encoding="utf-8")
    assert "window.print()" in js


def test_platzhalter_vorlage_zeigt_vorlage_folgt_ohne_blatt(dist: Path):
    html = seite(dist, "wimmelbild")

    assert "Vorlage folgt" in html
    assert blaetter(html) == []
    assert "data-drucken" not in html


def test_noch_nicht_gebaute_vorlage_zeigt_vorlage_folgt(dist: Path):
    vorlagen_dir = Path(__file__).parents[1] / "templates" / "vorlagen"
    offen = [
        v.id
        for v in load_site().druckvorlagen
        if v.status != "platzhalter" and not (vorlagen_dir / f"{v.id}.html").exists()
    ]
    if not offen:
        pytest.skip("alle Druckvorlagen sind gebaut")

    assert "Vorlage folgt" in seite(dist, offen[0])


def test_druckvorlage_verlinkt_ihre_methoden(dist: Path):
    html = seite(dist, "wettersymbole")

    assert '<a href="/methoden/wetterbericht/">Wetterbericht</a>' in html
    assert '<a href="/methoden/klebepunkte/">' in html


def test_druck_css_a4_ohne_bedienelemente_und_werbung(dist: Path):
    css = (dist / "static" / "css" / "druckvorlage.css").read_text(encoding="utf-8")

    assert re.search(r"@page\s*\{\s*size:\s*A4;\s*margin:\s*12mm;?\s*\}", css)
    druck = css[css.index("@media print") :]
    for selektor in (".vorlage-kopf", ".werbeplatz"):
        assert selektor in druck
    assert "break-after: page" in druck
    assert "dashed" in css


def test_jedes_blatt_traegt_fusstext_mit_name_und_domain(dist: Path):
    html = seite(dist, "exit-ticket")

    for blatt in blaetter(html):
        assert "Feedback-Tools · example.org" in blatt


def test_zielscheibe_einzel_und_plakat_mit_4_ringen_und_6_beschriftungsfeldern(dist: Path):
    html = seite(dist, "zielscheibe")

    einzel, plakat = blaetter(html)
    for blatt in (einzel, plakat):
        assert blatt.count('class="scheibe__ring"') == 4
        assert blatt.count('class="scheibe__teiler"') == 6
        assert blatt.count('class="scheibe__feld"') == 6
    assert "Einzel (A4)" in einzel
    assert "Plakatversion (A3-tauglich)" in plakat


def test_lernrad_ein_blatt_mit_6_bis_8_segmenten_4_stufen_und_hinweis(dist: Path):
    html = seite(dist, "lernrad")

    (blatt,) = blaetter(html)
    assert blatt.count('class="scheibe__ring"') == 4
    segmente = blatt.count('class="scheibe__teiler"')
    assert 6 <= segmente <= 8
    assert blatt.count('class="scheibe__feld"') == segmente
    assert "Wird noch geprüft" in html


def test_wettersymbole_vier_quer_blaetter_und_eine_seite_mini_karten(dist: Path):
    html = seite(dist, "wettersymbole")

    *gross, karten = blaetter(html)
    assert len(gross) == 4
    namen = ("Sonne", "Sonne mit Wolke", "Wolke", "Gewitter")
    for blatt, name in zip(gross, namen, strict=True):
        assert blatt.startswith(" blatt--quer")
        assert blatt.count('<svg class="wetter"') == 1
        assert f'aria-label="{name}"' in blatt
    assert not karten.startswith(" blatt--quer")
    assert karten.count('class="mini-karte"') == 8
    for name in namen:
        assert karten.count(f'aria-label="{name}"') == 2


def test_eckenschilder_vier_quer_blaetter_mit_buchstabe_und_leerem_feld(dist: Path):
    html = seite(dist, "eckenschilder")

    schilder = blaetter(html)
    assert len(schilder) == 4
    for blatt, buchstabe in zip(schilder, "ABCD", strict=True):
        assert blatt.startswith(" blatt--quer")
        assert f'<p class="eckenschild__buchstabe">{buchstabe}</p>' in blatt
        assert '<div class="eckenschild__feld"></div>' in blatt


def test_skalen_plakat_hat_plakat_quer_und_sechs_bodenkarten_a5(dist: Path):
    html = seite(dist, "skalen-plakat")

    plakat, *bodenkarten = blaetter(html)
    assert len(bodenkarten) == 3
    assert plakat.startswith(' blatt--quer"')
    assert plakat.count('class="skala__stufe"') == 6
    assert plakat.count('class="skala__punkte"') == 6
    for zahl in "123456":
        assert f'<span class="skala__zahl">{zahl}</span>' in plakat
    karten = re.findall(r'<span class="bodenkarte__zahl">(\d)</span>', "".join(bodenkarten))
    assert karten == list("123456")
    for blatt in bodenkarten:
        assert blatt.count('class="bodenkarte"') == 2


def test_quer_blaetter_drucken_auf_a4_quer(dist: Path):
    css = (dist / "static" / "css" / "druckvorlage.css").read_text(encoding="utf-8")

    assert re.search(r"@page\s+quer\s*\{\s*size:\s*A4 landscape;", css)
    assert re.search(r"\.blatt--quer\s*\{[^}]*page:\s*quer;", css)
    assert len(re.findall(r"@page\s+quer\b", css)) == 1


def test_checkliste_ist_tabelle_mit_acht_leeren_ich_kann_zeilen(dist: Path):
    html = seite(dist, "checkliste")

    (blatt,) = blaetter(html)
    kopf = re.findall(r'<th scope="col">(.*?)</th>', blatt)
    assert kopf == ["Ich kann …", "sicher", "teilweise", "noch nicht", "Übung dazu"]
    tbody = blatt[blatt.index("<tbody>") : blatt.index("</tbody>")]
    assert tbody.count("<tr>") == 8
    assert tbody.count('class="ankreuzfeld"') == 8 * 3
