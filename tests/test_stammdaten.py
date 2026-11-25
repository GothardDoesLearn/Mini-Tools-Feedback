from pathlib import Path

import pytest

import build as build_cli
from generator import paths
from generator.content import ContentError, load_site
from tests.test_methoden import GUELTIGE_METHODE, content_mit_methode


def test_stammdaten_werden_mit_schema_geladen():
    site = load_site()

    assert [k.id for k in site.kategorien] == ["A", "B", "C", "D", "E", "F", "G"]
    assert site.kategorien[0].titel == "Handzeichen & Karten"
    assert [g.feld for g in site.filter] == [
        "kategorie",
        "richtung",
        "zeitpunkt",
        "form",
        "druckvorlage",
    ]
    richtung = site.filter[1]
    assert richtung.werte[0].id == "sus-an-lehrkraft"
    assert {t.id for t in site.tools} == {"oncoo", "mentimeter", "plickers", "kahoot", "edkimo"}
    assert len(site.methoden) == 31


def test_unbekanntes_feld_in_stammdaten_bricht_ab(tmp_path: Path):
    content_dir = content_mit_methode(tmp_path, "test-methode.md", GUELTIGE_METHODE)
    tools = content_dir / "tools.yaml"
    tools.write_text(
        tools.read_text(encoding="utf-8").replace("  titel: Oncoo\n", "  titell: Oncoo\n"),
        encoding="utf-8",
    )

    with pytest.raises(ContentError, match=r"(?s)tools\.yaml.*titel"):
        load_site(content_dir)


TOOLS_YAML = """\
- id: test-tool
  titel: Testtool
  url: https://example.org
  zweck: Testen
  ablauf: Testen
  sus_geraete: "ja"
  methoden: [test-methode]
"""

DRUCKVORLAGEN_YAML = """\
- id: test-vorlage
  titel: Testvorlage
  methoden: [test-methode]
  inhalt: Testinhalt
  seiten: "1"
  status: fertig
"""


def content_mit_querverweisen(tmp_path: Path, methode: str = GUELTIGE_METHODE) -> Path:
    """Eine Methode plus tools.yaml/druckvorlagen.yaml, die nur auf diese Methode zeigen."""
    content_dir = content_mit_methode(tmp_path, "test-methode.md", methode)
    (content_dir / "tools.yaml").write_text(TOOLS_YAML, encoding="utf-8")
    (content_dir / "druckvorlagen.yaml").write_text(DRUCKVORLAGEN_YAML, encoding="utf-8")
    return content_dir


def test_gueltige_querverweise_werden_akzeptiert(tmp_path: Path):
    methode = GUELTIGE_METHODE.replace(
        "status: fertig", 'status: fertig\ntools: ["test-tool"]\nverwandt: ["test-methode"]'
    )

    site = load_site(content_mit_querverweisen(tmp_path, methode))

    assert site.methoden[0].tools == ["test-tool"]


def test_unbekannte_tool_id_bricht_mit_klarer_meldung_ab(tmp_path: Path):
    methode = GUELTIGE_METHODE.replace("status: fertig", 'status: fertig\ntools: ["padlet"]')

    with pytest.raises(ContentError, match=r"test-methode\.md: tools 'padlet' ist unbekannt"):
        load_site(content_mit_querverweisen(tmp_path, methode))


def test_unbekannte_methoden_id_in_verwandt_bricht_mit_klarer_meldung_ab(tmp_path: Path):
    methode = GUELTIGE_METHODE.replace(
        "status: fertig", 'status: fertig\nverwandt: ["gibts-nicht"]'
    )

    with pytest.raises(
        ContentError, match=r"test-methode\.md: verwandt 'gibts-nicht' ist unbekannt"
    ):
        load_site(content_mit_querverweisen(tmp_path, methode))


def test_unbekannte_methoden_id_in_tools_yaml_bricht_ab(tmp_path: Path):
    content_dir = content_mit_querverweisen(tmp_path)
    (content_dir / "tools.yaml").write_text(
        TOOLS_YAML.replace("[test-methode]", "[gibts-nicht]"), encoding="utf-8"
    )

    with pytest.raises(
        ContentError, match=r"tools\.yaml: test-tool: methoden 'gibts-nicht' ist unbekannt"
    ):
        load_site(content_dir)


@pytest.mark.parametrize("modus", [["--check"], ["--out"]])
def test_check_und_build_brechen_bei_unbekannter_tool_id_ab(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    modus: list[str],
):
    methode = GUELTIGE_METHODE.replace("status: fertig", 'status: fertig\ntools: ["padlet"]')
    monkeypatch.setattr(paths, "CONTENT_DIR", content_mit_querverweisen(tmp_path, methode))
    argv = modus + [str(tmp_path / "dist")] if modus == ["--out"] else modus

    exitcode = build_cli.main(argv)

    assert exitcode == 1
    assert "test-methode.md: tools 'padlet' ist unbekannt" in capsys.readouterr().err
    assert not (tmp_path / "dist").exists()
