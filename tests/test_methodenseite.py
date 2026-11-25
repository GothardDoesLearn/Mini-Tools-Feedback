"""Methodenseite (Issue #7): Kopf, Kurzinfos, Hinweisbox, Anleitung."""

import re
from pathlib import Path

import pytest

from generator.build import build, make_env
from generator.config import load_config
from generator.content import load_site
from generator.methodenseite import kontext


@pytest.fixture(scope="module")
def dist(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return out


def seite(dist: Path, methoden_id: str) -> str:
    return (dist / "methoden" / methoden_id / "index.html").read_text(encoding="utf-8")


def test_alle_31_methodenseiten_werden_gebaut(dist: Path):
    seiten = sorted(p.parent.name for p in (dist / "methoden").glob("*/index.html"))
    assert len(seiten) == 31
    assert "daumenprobe" in seiten


def test_kopf_zeigt_kategorie_titel_und_ersten_ablaufschritt_als_nutzen(dist: Path):
    html = seite(dist, "daumenprobe")
    assert "Daumenprobe</h1>" in html
    assert "Handzeichen &amp; Karten" in html
    assert (
        '<p class="methode__nutzen">Lehrkraft stellt eine Ja/Nein- oder Einschätzungsfrage '
        "(„Konntet ihr der Erklärung folgen?“).</p>"
    ) in html


def test_brotkrumen_fuehren_zur_uebersicht(dist: Path):
    html = seite(dist, "daumenprobe")
    assert 'aria-label="Brotkrumen"' in html
    assert '<a href="/">Methoden</a>' in html
    assert '<a href="/kategorien/handzeichen-karten/">Handzeichen &amp; Karten</a>' in html
    assert '<span aria-current="page">Daumenprobe</span>' in html


def hinweisbox(html: str) -> str | None:
    treffer = re.search(r'<p class="statushinweis[^"]*" role="note">(.*?)</p>', html, re.S)
    return treffer and " ".join(treffer.group(1).split())


def test_fertige_methode_hat_keine_hinweisbox(dist: Path):
    assert hinweisbox(seite(dist, "daumenprobe")) is None


def test_annahme_zeigt_hinweisbox_mit_hinweistext(dist: Path):
    box = hinweisbox(seite(dist, "fahrstuhlmethode"))
    assert box.startswith(
        "<strong>Wird noch geprüft:</strong> Methode aus dem Kollegium. "
        "Der Ablauf ist eine Vermutung und wird noch geprüft."
    )


def test_platzhalter_zeigt_hinweisbox_als_platzhalter(dist: Path):
    box = hinweisbox(seite(dist, "wimmelbild-zuordnen"))
    assert box.startswith("<strong>Platzhalter:</strong> Platzhalter – Ablauf und Bild")


@pytest.mark.parametrize(
    ("status", "erwartet"),
    [
        ("annahme", "<strong>Wird noch geprüft:</strong> Der Ablauf wird noch geprüft."),
        (
            "platzhalter",
            "<strong>Platzhalter:</strong> Dieser Inhalt fehlt noch und folgt nach Rücksprache.",
        ),
    ],
)
def test_statushinweis_ohne_hinweistext_nutzt_standardtext_je_status(status, erwartet):
    env = make_env(load_config())
    html = env.from_string(
        '{% from "_statushinweis.html" import statushinweis %}{{ statushinweis(s) }}'
    ).render(s=status)
    assert hinweisbox(html) == erwartet


def test_kurzinfos_mit_labels_aus_den_stammdaten(dist: Path):
    html = seite(dist, "daumenprobe")
    dl = re.search(r'<dl class="kurzinfos".*?</dl>', html, re.S).group(0)
    paare = re.findall(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", dl, re.S)
    assert paare == [
        ("Dauer", "ca. 1 Min"),
        ("Wann", "Zwischendurch"),
        ("Form", "Analog"),
        ("Richtung", "SuS → Lehrkraft, Selbsteinschätzung"),
        ("Material", "kein Material"),
    ]


def abschnitte(html: str) -> list[tuple[str, str, str]]:
    """(Klassen, Überschrift, Inhalt) jedes Anleitungsabschnitts."""
    return re.findall(
        r'<section class="anleitung__abschnitt ([^"]*)"[^>]*>\s*<h2[^>]*>(.*?)</h2>(.*?)</section>',
        html,
        re.S,
    )


def test_anleitung_mit_ablauf_als_nummerierte_schritte_und_tipps_als_zettel(dist: Path):
    teile = abschnitte(seite(dist, "daumenprobe"))
    assert [(klassen, titel) for klassen, titel, _ in teile] == [
        ("anleitung__abschnitt--ablauf", "Ablauf"),
        ("anleitung__abschnitt--tipps anleitung__zettel", "Tipps"),
    ]
    ablauf = teile[0][2]
    assert ablauf.count("<li>") == 3
    assert "<ol>" in ablauf
    assert "Augen schließen lassen" in teile[1][2]


def test_einleitung_steht_vor_dem_ablauf_und_varianten_sind_zettel(dist: Path):
    teile = abschnitte(seite(dist, "5-finger-methode"))
    assert [titel for _, titel, _ in teile] == ["Ablauf", "Varianten"]
    ablauf = teile[0][2]
    assert ablauf.index("<strong>Daumen:</strong>") < ablauf.index("<ol>")
    assert "anleitung__zettel" in teile[1][0]


@pytest.fixture(scope="module")
def css(dist: Path) -> str:
    return (dist / "static" / "css" / "site.css").read_text(encoding="utf-8")


def media_bloecke(css: str, query: str) -> str:
    teile = []
    for m in re.finditer(rf"@media {re.escape(query)}\s*\{{", css):
        tiefe = 0
        for i in range(m.end() - 1, len(css)):
            tiefe += {"{": 1, "}": -1}.get(css[i], 0)
            if tiefe == 0:
                teile.append(css[m.end() : i])
                break
    return "".join(teile)


def test_spalten_mobil_untereinander_ab_desktop_nebeneinander(dist: Path, css: str):
    html = seite(dist, "daumenprobe")
    assert html.index('class="methode__haupt') < html.index('<aside class="methode__seite"')
    grundregel = re.search(r"\.methode__spalten\s*\{([^}]*)\}", css).group(1)
    assert "grid-template-columns" not in grundregel
    desktop = media_bloecke(css, "(min-width: 960px)")
    regel = re.search(r"\.methode__spalten\s*\{([^}]*)\}", desktop).group(1)
    assert re.search(r"grid-template-columns:\s*minmax\(0,\s*\S+\)\s+\S+", regel)


def test_druckansicht_ohne_navigation_und_seitenleiste(css: str):
    druck = media_bloecke(css, "print")
    for selektor in (".methode__zurueck", ".methode__seite", "nav"):
        assert selektor in druck, selektor


def test_kopf_nimmt_feld_kurz_wenn_gefuellt():
    site = load_site()
    methode = next(m for m in site.methoden if m.id == "daumenprobe")
    ctx = kontext(methode.model_copy(update={"kurz": "Ein Satz."}), site)
    assert ctx["nutzen"] == "Ein Satz."
    assert ctx["seitentitel"] == "Daumenprobe"
