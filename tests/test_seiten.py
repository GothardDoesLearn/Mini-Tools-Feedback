"""Über-Seite, Impressum und Datenschutz (Issue #34): Inhalte aus content/seiten/."""

import re
import shutil
from pathlib import Path

import pytest

from generator import paths
from generator.build import build
from generator.content import ContentError, load_seiten

SEITEN = ("ueber", "impressum", "datenschutz")


@pytest.fixture(scope="module")
def dist(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return out


def seite(dist: Path, url: str) -> str:
    return (dist / url / "index.html").read_text(encoding="utf-8")


def schreibe_seite(tmp_path: Path, name: str, text: str) -> Path:
    (tmp_path / "seiten").mkdir(exist_ok=True)
    (tmp_path / "seiten" / name).write_text(text, encoding="utf-8")
    return tmp_path


def test_load_seiten_liest_alle_seiten_aus_content():
    seiten = {s.id: s for s in load_seiten()}
    assert set(SEITEN) <= set(seiten)
    for s in seiten.values():
        assert s.titel and s.body


def test_impressum_und_datenschutz_sind_platzhalter():
    seiten = {s.id: s for s in load_seiten()}
    assert seiten["impressum"].status == "platzhalter"
    assert seiten["datenschutz"].status == "platzhalter"


def test_unbekannter_status_bricht_ab(tmp_path: Path):
    content = schreibe_seite(
        tmp_path, "test.md", "---\nid: test\ntitel: Test\nstatus: egal\n---\nText\n"
    )
    with pytest.raises(ContentError, match="test.md"):
        load_seiten(content)


def test_id_muss_dateinamen_entsprechen(tmp_path: Path):
    content = schreibe_seite(
        tmp_path, "test.md", "---\nid: anders\ntitel: Test\nstatus: fertig\n---\nText\n"
    )
    with pytest.raises(ContentError, match="Dateinamen"):
        load_seiten(content)


@pytest.mark.parametrize("url", SEITEN)
def test_seite_wird_gebaut_und_ist_im_fuss_verlinkt(dist: Path, url: str):
    html = seite(dist, url)
    titel = {s.id: s.titel for s in load_seiten()}[url]
    assert f"<h1>{titel}</h1>" in html
    for andere in ("", *SEITEN):
        fuss = re.search(r"<footer.*?</footer>", seite(dist, andere), re.S).group(0)
        assert f'href="/{url}/"' in fuss


@pytest.mark.parametrize("url", ["impressum", "datenschutz"])
def test_platzhalter_sind_sichtbar_gekennzeichnet(dist: Path, url: str):
    html = seite(dist, url)
    box = re.search(r'<(div|aside)[^>]*class="hinweisbox[^"]*".*?</\1>', html, re.S)
    assert box, url
    assert "Platzhalter" in box.group(0)


def test_ueber_seite_nennt_lizenzen_nach_adr_0002(dist: Path):
    html = seite(dist, "ueber")
    assert "CC BY-NC-SA 4.0" in html
    assert "MIT" in html
    assert "creativecommons.org/licenses/by-nc-sa/4.0/" in html


def test_ueber_seite_markiert_aktiven_menuepunkt(dist: Path):
    html = seite(dist, "ueber")
    assert re.search(r'href="/ueber/"[^>]*aria-current="page"', html)


def test_seite_im_status_fertig_hat_keine_hinweisbox(tmp_path: Path, monkeypatch):
    content = tmp_path / "content"
    shutil.copytree(paths.CONTENT_DIR, content)
    for datei in (content / "seiten").glob("*.md"):
        text = datei.read_text(encoding="utf-8")
        datei.write_text(re.sub(r"status: \w+", "status: fertig", text, count=1), "utf-8")
    monkeypatch.setattr(paths, "CONTENT_DIR", content)
    build(output_dir=tmp_path / "dist")
    assert 'class="hinweisbox' not in seite(tmp_path / "dist", "impressum")
