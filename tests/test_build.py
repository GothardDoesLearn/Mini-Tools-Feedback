from pathlib import Path

from generator.build import build
from generator.css import stylesheet
from generator.seiten import alle_seiten


def test_build_erzeugt_startseite_mit_website_name(tmp_path: Path):
    build(output_dir=tmp_path)

    index = tmp_path / "index.html"
    assert index.is_file()
    html = index.read_text(encoding="utf-8")
    assert '<html lang="de"' in html
    assert "<title>Feedback-Tools</title>" in html


def test_stylesheet_ordner_werden_zusammengehaengt_statt_kopiert(tmp_path: Path):
    build(output_dir=tmp_path)

    css = tmp_path / "static" / "css"
    for name in ("site", "druckvorlage"):
        assert not (css / name).exists()
        assert (css / f"{name}.css").read_text(encoding="utf-8") == stylesheet(name)
    # Reihenfolge = Dateinamen: Tokens vor Pinnwand vor Druck
    text = stylesheet("site")
    assert text.index("--abstand-") < text.index("--pin-logo:") < text.index("@media print")


def test_jede_seite_ist_genau_einmal_angemeldet():
    namen = [f"{f.__module__}.{f.__name__}" for f in alle_seiten()]
    assert len(namen) == len(set(namen))
    assert "generator.seiten.startseite.startseite" in namen
