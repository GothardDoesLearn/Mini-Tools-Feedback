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
    html = seite(dist, "feedback-hand")

    assert "Vorlage folgt" in html


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


REFLEXIONS_SATZANFAENGE = (
    "Am meisten geholfen hat mir …",
    "Schwierig war …",
    "Nächstes Mal mache ich …",
    "Überrascht hat mich …",
    "Ich bin stolz auf …",
    "Ich brauche noch …",
    "Am besten gelernt habe ich durch …",
    "Das will ich noch wissen …",
    "Unsere Zusammenarbeit war …",
    "Mein Ziel war …",
    "Das nehme ich mit …",
    "Joker",
)


def test_reflexionskarten_zwoelf_karten_auf_einem_blatt(dist: Path):
    (blatt,) = blaetter(seite(dist, "reflexionskarten"))
    blatt = blatt.replace(" ", " ")  # geschütztes Leerzeichen vor „…“

    assert blatt.count('class="reflexionskarte"') == 12
    for satzanfang in REFLEXIONS_SATZANFAENGE:
        assert f">{satzanfang}<" in blatt


WUERFEL_FRAGEN = (
    "Was war neu?",
    "Was war schwer?",
    "Was hat Spaß gemacht?",
    "Was willst du noch wissen?",
    "Wie hast du gearbeitet?",
    "Joker",
)


def ohne_tags(html: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def test_wuerfelnetz_mit_fragen_und_leerem_netz(dist: Path):
    beschriftet, leer = blaetter(seite(dist, "wuerfelnetz"))

    for netz in (beschriftet, leer):
        assert netz.count('class="wuerfel__seite"') == 6
        assert netz.count('class="wuerfel__lasche"') == 7  # 12 Kanten − 5 Falzkanten im Netz
    text = ohne_tags(beschriftet)
    for frage in WUERFEL_FRAGEN:
        assert frage in text
        assert frage not in ohne_tags(leer)


def test_fragebogen_acht_aussagen_mit_skala_und_zwei_offene_fragen(dist: Path):
    (blatt,) = blaetter(seite(dist, "fragebogen"))

    assert blatt.count('class="fragebogen__aussage"') == 8
    for aussage in (
        "Die Aufgaben waren verständlich",
        "Ich konnte Fragen stellen",
        "Das Tempo war passend",
        "Ich weiß, was ich lernen soll",
    ):
        assert f">{aussage}<" in blatt
    assert blatt.count('class="fragebogen__kreuz"') == 8 * 4
    for stufe in "1234":
        assert f'<th scope="col">{stufe}</th>' in blatt
    for frage in ("Was soll bleiben?", "Was soll sich ändern?"):
        assert f"{frage}</p>" in blatt


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


def test_quer_blaetter_drucken_auf_a4_quer(dist: Path):
    css = (dist / "static" / "css" / "druckvorlage.css").read_text(encoding="utf-8")

    assert re.search(r"@page\s+quer\s*\{\s*size:\s*A4 landscape;", css)
    assert re.search(r"\.blatt--quer\s*\{[^}]*page:\s*quer;", css)
