"""PRD §9.6: Eine neue Methode entsteht durch Anlegen einer einzigen .md-Datei (Issue #38)."""

import shutil
from pathlib import Path

import pytest

from generator import paths
from generator.build import build
from generator.paths import CONTENT_DIR
from tests.test_links import tote_links
from tests.test_methoden import GUELTIGE_METHODE


def test_neue_methode_braucht_nur_eine_md_datei(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    content = tmp_path / "content"
    shutil.copytree(CONTENT_DIR, content)
    (content / "methoden" / "test-methode.md").write_text(GUELTIGE_METHODE, encoding="utf-8")
    monkeypatch.setattr(paths, "CONTENT_DIR", content)

    build(output_dir=tmp_path / "dist")

    dist = tmp_path / "dist"
    seite = (dist / "methoden" / "test-methode" / "index.html").read_text(encoding="utf-8")
    assert "Testmethode" in seite
    for uebersicht in (dist / "index.html", dist / "kategorien"):
        dateien = [uebersicht] if uebersicht.is_file() else uebersicht.rglob("index.html")
        assert any(
            'href="/methoden/test-methode/"' in d.read_text(encoding="utf-8") for d in dateien
        ), uebersicht
    assert tote_links(dist) == []
