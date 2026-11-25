from pathlib import Path

import pytest

import build as build_cli
from generator import paths
from generator.content import ContentError, load_site
from tests.test_methoden import GUELTIGE_METHODE
from tests.test_stammdaten import content_mit_querverweisen


def test_alle_druckvorlagen_werden_mit_schema_geladen():
    site = load_site()

    assert len(site.druckvorlagen) == 18
    hand = site.druckvorlagen[0]
    assert hand.id == "feedback-hand"
    assert hand.titel == "Feedback-Hand"
    assert hand.seiten == "1"
    assert hand.status == "fertig"
    ampel = next(v for v in site.druckvorlagen if v.id == "ampelkarten")
    assert ampel.seiten == "3 (je Farbe 1)"
    assert ampel.inhalt == (
        '3 Karten pro SuS (rot/gelb/grün) im Format A7; zusätzlich Text "Hilfe" / '
        '"unsicher" / "verstanden" für SW-Druck; 4 Sätze pro Seite'
    )
    status = {v.id: v.status for v in site.druckvorlagen if v.status != "fertig"}
    assert status == {"lernrad": "annahme", "wimmelbild": "platzhalter"}


def test_jede_druckvorlage_einer_methode_existiert():
    site = load_site()

    vorlagen_ids = {v.id for v in site.druckvorlagen}
    for methode in site.methoden:
        assert set(methode.druckvorlagen) <= vorlagen_ids


def test_unbekannte_druckvorlagen_id_bricht_mit_klarer_meldung_ab(tmp_path: Path):
    methode = GUELTIGE_METHODE.replace("druckvorlagen: []", 'druckvorlagen: ["gibts-nicht"]')

    with pytest.raises(
        ContentError, match=r"test-methode\.md: druckvorlagen 'gibts-nicht' ist unbekannt"
    ):
        load_site(content_mit_querverweisen(tmp_path, methode))


def test_methoden_einer_druckvorlage_kommen_aus_den_methodendateien():
    # PRD §9.6: eine neue Methode = eine .md-Datei; druckvorlagen.yaml nennt keine Methoden.
    site = load_site()

    assert [m.id for m in site.methoden_mit_vorlage("feedback-hand")] == ["5-finger-methode"]
    # nach Titel sortiert (DIN 5007)
    assert [m.titel for m in site.methoden_mit_vorlage("wettersymbole")] == [
        "Klebepunkte",
        "Wetterbericht",
    ]


def test_druckvorlage_ohne_methode_bricht_ab(tmp_path: Path):
    content_dir = content_mit_querverweisen(tmp_path)
    datei = content_dir / "druckvorlagen.yaml"
    datei.write_text(
        datei.read_text(encoding="utf-8").replace("test-vorlage", "verwaist"), encoding="utf-8"
    )

    with pytest.raises(
        ContentError, match=r"druckvorlagen\.yaml: verwaist: keine Methode nennt diese Vorlage"
    ):
        load_site(content_dir)


def test_unbekannter_status_in_druckvorlagen_yaml_bricht_ab(tmp_path: Path):
    content_dir = content_mit_querverweisen(tmp_path)
    datei = content_dir / "druckvorlagen.yaml"
    datei.write_text(
        datei.read_text(encoding="utf-8").replace("status: fertig", "status: fast"),
        encoding="utf-8",
    )

    with pytest.raises(ContentError, match=r"(?s)druckvorlagen\.yaml.*status"):
        load_site(content_dir)


@pytest.mark.parametrize("modus", [["--check"], ["--out"]])
def test_check_und_build_brechen_bei_unbekannter_druckvorlage_ab(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    modus: list[str],
):
    methode = GUELTIGE_METHODE.replace("druckvorlagen: []", 'druckvorlagen: ["gibts-nicht"]')
    monkeypatch.setattr(paths, "CONTENT_DIR", content_mit_querverweisen(tmp_path, methode))
    argv = modus + [str(tmp_path / "dist")] if modus == ["--out"] else modus

    exitcode = build_cli.main(argv)

    assert exitcode == 1
    assert "test-methode.md: druckvorlagen 'gibts-nicht' ist unbekannt" in capsys.readouterr().err
    assert not (tmp_path / "dist").exists()
