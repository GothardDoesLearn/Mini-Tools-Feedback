"""Methodenseite (Issue #9): Video-Bereich mit Zwei-Klick-Einbettung (ADR 0001).

Testdaten: eine Kopie von content/, in der die Daumenprobe ein Video bekommt
(nichts davon wird in content/ committet).
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from generator import paths
from generator.build import build
from tests.test_cli import DRITTSERVER_RESSOURCE

VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.fixture(scope="module")
def dist_mit_video(tmp_path_factory) -> Path:
    tmp = tmp_path_factory.mktemp("video")
    content = tmp / "content"
    shutil.copytree(paths.CONTENT_DIR, content)
    datei = content / "methoden" / "daumenprobe.md"
    text = datei.read_text(encoding="utf-8")
    videos = f'videos:\n  - titel: "Daumenprobe im Unterricht"\n    url: "{VIDEO_URL}"\n'
    datei.write_text(text.replace("status: fertig\n", "status: fertig\n" + videos, 1), "utf-8")

    alt = paths.CONTENT_DIR
    paths.CONTENT_DIR = content
    try:
        build(output_dir=tmp / "dist")
    finally:
        paths.CONTENT_DIR = alt
    return tmp / "dist"


@pytest.fixture(scope="module")
def seite(dist_mit_video: Path) -> str:
    return (dist_mit_video / "methoden" / "daumenprobe" / "index.html").read_text("utf-8")


def _video_bereich(html: str) -> str:
    return re.search(r'<section class="video".*?</section>', html, re.S).group(0)


def test_ohne_videos_erscheint_kein_video_bereich(dist_mit_video: Path):
    html = (dist_mit_video / "methoden" / "ampel" / "index.html").read_text("utf-8")
    assert 'class="video' not in html
    assert "video.js" not in html


def test_video_bereich_steht_in_der_linken_spalte_unter_den_zetteln(seite: str):
    haupt = seite[seite.index('class="methode__haupt') : seite.index("methode__seite")]
    assert '<section class="video"' in haupt
    assert haupt.index("anleitung__zettel") < haupt.index('<section class="video"')


def test_vorschau_mit_hinweis_und_link_auf_youtube(seite: str):
    bereich = _video_bereich(seite)
    assert "Daumenprobe im Unterricht" in bereich
    assert "Beim Abspielen werden Daten an YouTube übertragen" in bereich
    assert re.search(r"<button [^>]*type=\"button\"", bereich)
    link = re.search(r'<a class="extern-link" href="([^"]+)"[^>]*>\s*Auf YouTube ansehen', bereich)
    assert link and link.group(1) == VIDEO_URL


def test_vor_dem_klick_keine_anfrage_an_youtube(seite: str):
    assert "<iframe" not in seite
    assert not DRITTSERVER_RESSOURCE.search(seite)
    # Auch kein Vorschaubild von YouTube (img.youtube.com / ytimg.com).
    assert "ytimg" not in seite and "img.youtube" not in seite


def test_einbettung_ueber_youtube_nocookie(seite: str):
    bereich = _video_bereich(seite)
    ziel = re.search(r'data-video-einbettung="([^"]+)"', bereich).group(1)
    assert ziel == "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?autoplay=1"
    assert '<script src="/static/js/video.js" defer></script>' in seite


@pytest.mark.parametrize(
    ("url", "video_id"),
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtube.com/watch?feature=share&v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ?si=abc", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://vimeo.com/123456", None),
        ("https://www.youtube.com/watch?v=<script>", None),
    ],
)
def test_youtube_id_aus_url(url: str, video_id: str | None):
    from generator.video import youtube_id

    assert youtube_id(url) == video_id


def test_nicht_youtube_url_wird_nur_als_link_gezeigt():
    from generator.content import Video
    from generator.video import anzeige

    v = anzeige(Video(titel="Anderes Video", url="https://vimeo.com/123456"))
    assert v.einbettung is None
    assert v.url == "https://vimeo.com/123456"


def test_vorschau_braucht_javascript_und_fehlt_im_druck(dist_mit_video: Path):
    css = (dist_mit_video / "static" / "css" / "site.css").read_text("utf-8")
    assert re.search(r"html:not\(\[data-js\]\) \.video__vorschau\s*\{\s*display:\s*none", css)
    druck = css[css.index("@media print") :]
    assert ".video" in druck[: druck.index("display: none")]


# --- Verhalten von video.js (Node + Mini-DOM) ---------------------------------------------

NODE = shutil.which("node")
braucht_node = pytest.mark.skipif(NODE is None, reason="Node.js nicht installiert")

STUB = r"""
const fs = require("fs");
const skript = fs.readFileSync(0, "utf8");
const erzeugt = [];
function element(tag, attrs = {}) {
  const el = {
    tagName: tag.toUpperCase(), attrs: { ...attrs }, kinder: [], listener: {}, fokussiert: false,
    setAttribute(k, v) { this.attrs[k] = String(v); },
    getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; },
    addEventListener(t, f) { (this.listener[t] = this.listener[t] || []).push(f); },
    replaceWith(neu) { this.ersetztDurch = neu; },
    focus() { this.fokussiert = true; },
  };
  Object.defineProperty(el, "src", { set(v) { el.attrs.src = v; } });
  Object.defineProperty(el, "title", { set(v) { el.attrs.title = v; } });
  return el;
}
const knopf = element("button", {
  "data-video-einbettung": "https://www.youtube-nocookie.com/embed/abc?autoplay=1",
  "data-video-titel": "Mein Video",
});
const document = {
  querySelectorAll: (s) => (s === "[data-video-einbettung]" ? [knopf] : []),
  createElement: (t) => { const e = element(t); erzeugt.push(e); return e; },
};
new Function("document", skript)(document);
const vorher = erzeugt.filter((e) => e.tagName === "IFRAME").length;
(knopf.listener.click || []).forEach((f) => f({ preventDefault() {} }));
const iframe = knopf.ersetztDurch;
process.stdout.write(JSON.stringify({
  vorher,
  iframe: iframe && { tag: iframe.tagName, attrs: iframe.attrs, fokussiert: iframe.fokussiert },
}));
"""


@braucht_node
def test_erst_der_klick_laedt_das_video():
    skript = (paths.STATIC_DIR / "js" / "video.js").read_text("utf-8")
    r = subprocess.run(
        [NODE, "-e", STUB], input=skript, capture_output=True, text=True, encoding="utf-8"
    )
    assert r.returncode == 0, r.stderr
    e = json.loads(r.stdout)
    assert e["vorher"] == 0
    assert e["iframe"]["tag"] == "IFRAME"
    attrs = e["iframe"]["attrs"]
    assert attrs["src"] == "https://www.youtube-nocookie.com/embed/abc?autoplay=1"
    assert attrs["title"] == "Mein Video"
    assert "allowfullscreen" in attrs
    assert e["iframe"]["fokussiert"] is True
