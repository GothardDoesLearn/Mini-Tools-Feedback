"""Redaktionelle Texte aus content/texte.yaml (Issue #76): Schema, Platzhalter, Build."""

import shutil
from pathlib import Path

import pytest

import build as build_cli
from generator import paths
from generator.build import build
from generator.config import load_config
from generator.content import ContentError, load_texte
from generator.paths import CONTENT_DIR


def _texte_mit(tmp_path: Path, alt: str, neu: str) -> Path:
    """Kopie von content/ mit genau einer Änderung in texte.yaml."""
    content_dir = tmp_path / "content"
    shutil.copytree(CONTENT_DIR, content_dir)
    datei = content_dir / "texte.yaml"
    text = datei.read_text(encoding="utf-8")
    assert text.count(alt) == 1, alt
    datei.write_text(text.replace(alt, neu), encoding="utf-8")
    return content_dir


def test_texte_werden_geladen():
    texte = load_texte()

    assert set(texte.status.methode) == {"annahme", "platzhalter"}
    assert set(texte.status.vorlage) == {"annahme", "platzhalter"}
    assert set(texte.status.seite) == {"entwurf", "platzhalter"}
    assert "{anzahl}" in texte.meta.vorlagen
    assert "{website_name}" in texte.fusszeile.text


@pytest.mark.parametrize(
    ("alt", "neu", "meldung"),
    [
        ("  link_andere: Video ansehen\n", "", r"video\.link_andere"),
        ("  link_andere: Video ansehen\n", '  link_andere: ""\n', r"video\.link_andere"),
        (
            "    entwurf:\n      marke: Entwurf\n      titel: Entwurf\n"
            "      text: Dieser Text ist ein Entwurf und noch nicht freigegeben.\n",
            "",
            r"Statustexte fehlen für: entwurf",
        ),
        ("{website_name} · Inhalte", "{name} · Inhalte", r"unbekannter Platzhalter \{name\}"),
        ("  tools: Digitale Tools", "  tools: Digitale {anzahl} Tools", r"meta\.tools"),
        ("Seite nicht gefunden", "Seite {nicht gefunden", r"geschweifte Klammern"),
        ("  link: Zur Übersicht", "  verweis: Zur Übersicht", r"seite_404\.verweis"),
    ],
    ids=[
        "fehlt",
        "leer",
        "status-fehlt",
        "unbekannter-platzhalter",
        "platzhalter-nicht-erlaubt",
        "offene-klammer",
        "unbekanntes-feld",
    ],
)
def test_fehler_in_texte_yaml_bricht_ab(tmp_path: Path, alt: str, neu: str, meldung: str):
    content_dir = _texte_mit(tmp_path, alt, neu)

    with pytest.raises(ContentError, match=rf"(?s)texte\.yaml.*{meldung}"):
        load_texte(content_dir)


def test_check_meldet_fehler_in_texte_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    content_dir = _texte_mit(tmp_path, "{website_name} · Inhalte", "{name} · Inhalte")
    monkeypatch.setattr(paths, "CONTENT_DIR", content_dir)

    assert build_cli.main(["--check"]) == 1
    fehlermeldung = capsys.readouterr().err
    assert "texte.yaml" in fehlermeldung
    assert "Traceback" not in fehlermeldung


def test_build_nimmt_texte_aus_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    content_dir = _texte_mit(
        tmp_path,
        'text: "{website_name} · Inhalte unter CC BY-NC-SA 4.0"',
        'text: "Testfuß von {website_name}"',
    )
    texte = (content_dir / "texte.yaml").read_text(encoding="utf-8")
    texte = texte.replace("Seite nicht gefunden", "Testfehlerseite")
    texte = texte.replace("Alle {anzahl} Druckvorlagen", "Genau {anzahl} Testvorlagen")
    (content_dir / "texte.yaml").write_text(texte, encoding="utf-8")
    monkeypatch.setattr(paths, "CONTENT_DIR", content_dir)
    config = load_config()
    dist = tmp_path / "dist"

    build(dist, config)

    startseite = (dist / "index.html").read_text(encoding="utf-8")
    assert f"<p>Testfuß von {config.website_name}</p>" in startseite
    assert "<h1>Testfehlerseite</h1>" in (dist / "404.html").read_text(encoding="utf-8")
    anzahl = len(list((dist / "vorlagen").glob("*/index.html")))
    vorlagen = (dist / "vorlagen" / "index.html").read_text(encoding="utf-8")
    assert f'content="Genau {anzahl} Testvorlagen' in vorlagen
