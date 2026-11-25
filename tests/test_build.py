from pathlib import Path

from generator.build import build


def test_build_erzeugt_startseite_mit_website_name(tmp_path: Path):
    build(output_dir=tmp_path)

    index = tmp_path / "index.html"
    assert index.is_file()
    html = index.read_text(encoding="utf-8")
    assert '<html lang="de"' in html
    assert "<title>Feedback-Tools</title>" in html
