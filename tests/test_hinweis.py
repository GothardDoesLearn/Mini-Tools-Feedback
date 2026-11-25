"""Hinweis-Links auf Methoden-, Vorlagen- und Über-Seite (PRD §5.8, Issue #59)."""

import html as html_modul
import re
import shutil
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
import yaml

from generator.build import build
from generator.config import load_config
from generator.content import ContentError, load_hinweise
from generator.hinweis import BEZUG_FELD, ISSUE_VORLAGE, github_url, mailto, zeichenreferenzen
from generator.paths import CONTENT_DIR

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def dist(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return out


def seite(dist: Path, url: str) -> str:
    return (dist / url / "index.html").read_text(encoding="utf-8")


def hinweis_abschnitt(html: str) -> str:
    treffer = re.search(r'<section class="hinweis" id="hinweis".*?</section>', html, re.S)
    assert treffer, "Hinweis-Links fehlen"
    return treffer.group(0)


def links(abschnitt: str) -> tuple[dict[str, list[str]], str]:
    """(Query-Parameter des GitHub-Links, dekodierter mailto-Link)."""
    hrefs = re.findall(r'href="([^"]*)"', abschnitt)
    github = next(h for h in hrefs if h.startswith("https://github.com/"))
    email = next(html_modul.unescape(h) for h in hrefs if h.startswith("&#"))
    return parse_qs(urlsplit(html_modul.unescape(github)).query), email


# --- URLs -----------------------------------------------------------------


def test_github_url_kodiert_umlaute_und_leerzeichen():
    url = github_url(
        "https://github.com/a/b/", "Hinweis zur Methode Schätz-Übung", "Methode: Ö (ö)"
    )
    assert url == (
        "https://github.com/a/b/issues/new?template=hinweis.yml"
        "&title=Hinweis%20zur%20Methode%20Sch%C3%A4tz-%C3%9Cbung"
        f"&{BEZUG_FELD}=Methode%3A%20%C3%96%20%28%C3%B6%29"
    )


def test_github_url_ohne_bezug_laesst_das_feld_weg():
    assert BEZUG_FELD not in github_url("https://github.com/a/b", "Hinweis zur Website")


def test_mailto_kodiert_den_betreff():
    assert mailto("x@y.de", "Hinweis zur Methode Daumen & Faust") == (
        "mailto:x@y.de?subject=Hinweis%20zur%20Methode%20Daumen%20%26%20Faust"
    )


def test_zeichenreferenzen_kodieren_jedes_zeichen():
    kodiert = zeichenreferenzen("a@b")
    assert kodiert == "&#97;&#64;&#98;"
    assert html_modul.unescape(kodiert) == "a@b"


# --- Seiten ---------------------------------------------------------------


def test_methodenseite_hat_beide_links_mit_vorausgefuelltem_bezug(dist: Path):
    abschnitt = hinweis_abschnitt(seite(dist, "methoden/daumenprobe"))
    parameter, email = links(abschnitt)
    assert parameter["template"] == [ISSUE_VORLAGE]
    assert parameter["title"] == ["Hinweis zur Methode Daumenprobe"]
    assert parameter[BEZUG_FELD] == ["Methode: Daumenprobe (daumenprobe)"]
    config = load_config()
    assert email == f"mailto:{config.kontakt_email}?subject=Hinweis%20zur%20Methode%20Daumenprobe"
    texte = load_hinweise()
    assert texte.link_github in abschnitt and texte.link_email in abschnitt
    assert 'rel="noopener noreferrer"' in abschnitt


def test_vorlagenseite_hat_beide_links_mit_vorausgefuelltem_bezug(dist: Path):
    parameter, email = links(hinweis_abschnitt(seite(dist, "vorlagen/exit-ticket")))
    assert parameter["title"] == ["Hinweis zur Druckvorlage Exit-Ticket"]
    assert parameter[BEZUG_FELD] == ["Druckvorlage: Exit-Ticket (exit-ticket)"]
    assert "subject=Hinweis%20zur%20Druckvorlage%20Exit-Ticket" in email


def test_platzhalter_vorlage_hat_ebenfalls_hinweis_links(dist: Path):
    vorlagen = yaml.safe_load((CONTENT_DIR / "druckvorlagen.yaml").read_text(encoding="utf-8"))
    platzhalter = next(v["id"] for v in vorlagen if v["status"] == "platzhalter")
    hinweis_abschnitt(seite(dist, f"vorlagen/{platzhalter}"))


def test_ueber_seite_hat_links_unter_kontakt_ohne_bezug(dist: Path):
    html = seite(dist, "ueber")
    abschnitt = hinweis_abschnitt(html)
    assert html.index("<h2>Kontakt</h2>") < html.index(abschnitt) < html.index("<h2>Lizenz</h2>")
    assert "<h2" not in abschnitt  # Überschrift ist „Kontakt“
    parameter, email = links(abschnitt)
    assert parameter["title"] == ["Hinweis zur Website"]
    assert BEZUG_FELD not in parameter
    assert "subject=Hinweis%20zur%20Website" in email
    assert "hinweis-links" not in html  # Marke wird ersetzt


@pytest.mark.parametrize("url", ["methoden/daumenprobe", "vorlagen/exit-ticket", "ueber"])
def test_email_adresse_steht_nicht_im_klartext(dist: Path, url: str):
    assert load_config().kontakt_email not in seite(dist, url)


def test_druck_blendet_hinweis_links_aus(dist: Path):
    css = (dist / "static" / "css" / "site.css").read_text(encoding="utf-8")
    druck = re.search(r"@media print\s*{\s*([^{]*){\s*display: none !important;", css).group(1)
    assert ".hinweis" in [s.strip() for s in druck.split(",")]


# --- Statushinweis bei annahme ---------------------------------------------


def statushinweis(html: str) -> str:
    return re.search(r'<p class="statushinweis[^"]*" role="note">.*?</p>', html, re.S).group(0)


def test_annahme_bittet_um_hinweis_und_verlinkt_die_hinweis_links(dist: Path):
    html = seite(dist, "methoden/fahrstuhlmethode")
    box = statushinweis(html)
    texte = load_hinweise()
    assert texte.bitte_annahme in box
    assert f'href="#hinweis">{texte.link_bitte_annahme}</a>' in box
    hinweis_abschnitt(html)


def test_platzhalter_bittet_nicht_um_hinweis(dist: Path):
    box = statushinweis(seite(dist, "methoden/wimmelbild-zuordnen"))
    assert "#hinweis" not in box


# --- Inhalte und Issue-Formular ----------------------------------------------


def test_unbekannter_platzhalter_in_hinweise_yaml_bricht_ab(tmp_path: Path):
    shutil.copy(CONTENT_DIR / "hinweise.yaml", tmp_path / "hinweise.yaml")
    datei = tmp_path / "hinweise.yaml"
    datei.write_text(
        datei.read_text(encoding="utf-8").replace("Methode {titel}", "Methode {name}"),
        encoding="utf-8",
    )
    with pytest.raises(ContentError, match="hinweise.yaml"):
        load_hinweise(tmp_path)


def test_issue_formular_passt_zu_den_links():
    formular = yaml.safe_load(
        (ROOT / ".github" / "ISSUE_TEMPLATE" / ISSUE_VORLAGE).read_text(encoding="utf-8")
    )
    assert formular["labels"] == ["needs-triage"]
    felder = {f["id"]: f for f in formular["body"] if "id" in f}
    assert set(felder) == {"art", BEZUG_FELD, "beschreibung"}
    assert felder["art"]["attributes"]["options"] == [
        "Fehler/Korrektur",
        "Ergänzung/Variante",
        "Rückfrage",
        "Neue Methode",
    ]
    assert felder["beschreibung"]["validations"]["required"] is True
    hinweistext = formular["body"][0]["attributes"]["value"]
    assert "keine Namen" in hinweistext and "öffentlich" in hinweistext
