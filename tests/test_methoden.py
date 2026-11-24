import shutil
from pathlib import Path

import pytest

import build as build_cli
from generator import paths
from generator.content import ContentError, load_methoden
from generator.paths import CONTENT_DIR

GUELTIGE_METHODE = """\
---
id: test-methode
titel: "Testmethode"
kategorie: A
richtung: ["sus-an-lehrkraft"]
zeitpunkt: ["stundenende"]
form: ["analog"]
dauer: "1 Min"
dauer_min: 1
dauer_max: 1
material: "keins"
druckvorlagen: []
status: fertig
---

## Ablauf

1. Testen.
"""


def content_mit_methode(tmp_path: Path, dateiname: str, text: str) -> Path:
    """Stammdaten aus content/ kopieren und genau eine Methodendatei anlegen."""
    content_dir = tmp_path / "content"
    shutil.copytree(CONTENT_DIR, content_dir, ignore=shutil.ignore_patterns("methoden"))
    (content_dir / "methoden").mkdir()
    (content_dir / "methoden" / dateiname).write_text(text, encoding="utf-8")
    return content_dir


def test_alle_methodendateien_sind_gueltig():
    methoden = load_methoden()

    assert len(methoden) == 31
    ampel = next(m for m in methoden if m.id == "ampel")
    assert ampel.titel == "Ampel"
    assert ampel.kategorie == "A"
    assert ampel.dauer_min == 1
    assert "## Ablauf" in ampel.body


def test_gueltige_methodendatei_wird_geladen(tmp_path: Path):
    content_dir = content_mit_methode(tmp_path, "test-methode.md", GUELTIGE_METHODE)

    [methode] = load_methoden(content_dir)

    assert methode.id == "test-methode"
    assert methode.kurz is None
    assert methode.videos == []


def test_id_muss_dem_dateinamen_entsprechen(tmp_path: Path):
    content_dir = content_mit_methode(tmp_path, "anderer-name.md", GUELTIGE_METHODE)

    with pytest.raises(ContentError, match=r"anderer-name\.md.*test-methode"):
        load_methoden(content_dir)


def test_unbekannte_kategorie_bricht_mit_verstaendlicher_meldung_ab(tmp_path: Path):
    text = GUELTIGE_METHODE.replace("kategorie: A", "kategorie: Z")
    content_dir = content_mit_methode(tmp_path, "test-methode.md", text)

    with pytest.raises(ContentError, match=r"test-methode\.md.*kategorie.*'Z'.*A, B"):
        load_methoden(content_dir)


@pytest.mark.parametrize(
    ("alt", "neu"),
    [
        ('richtung: ["sus-an-lehrkraft"]', 'richtung: ["schueler"]'),
        ('zeitpunkt: ["stundenende"]', 'zeitpunkt: ["mittags"]'),
        ('form: ["analog"]', 'form: ["hybrid"]'),
    ],
)
def test_unbekannte_filterwerte_brechen_ab(tmp_path: Path, alt: str, neu: str):
    content_dir = content_mit_methode(
        tmp_path, "test-methode.md", GUELTIGE_METHODE.replace(alt, neu)
    )

    with pytest.raises(ContentError, match=r"test-methode\.md"):
        load_methoden(content_dir)


def test_fehlendes_pflichtfeld_nennt_datei_und_feld(tmp_path: Path):
    text = GUELTIGE_METHODE.replace('titel: "Testmethode"\n', "")
    content_dir = content_mit_methode(tmp_path, "test-methode.md", text)

    with pytest.raises(ContentError, match=r"(?s)test-methode\.md.*titel"):
        load_methoden(content_dir)


def test_check_kommando_meldet_schemafehler_ohne_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    text = GUELTIGE_METHODE.replace("kategorie: A", "kategorie: Z")
    monkeypatch.setattr(
        paths, "CONTENT_DIR", content_mit_methode(tmp_path, "test-methode.md", text)
    )

    exitcode = build_cli.main(["--check"])

    assert exitcode == 1
    fehlermeldung = capsys.readouterr().err
    assert "test-methode.md: kategorie 'Z' ist unbekannt" in fehlermeldung
    assert "Traceback" not in fehlermeldung
