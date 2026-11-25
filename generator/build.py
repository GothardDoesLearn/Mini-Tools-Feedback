"""Baut die Website: Konfiguration laden, Seiten rendern, statische Dateien kopieren.

Die Seiten melden sich selbst an (`@seite` in generator/seiten/), Stylesheets entstehen aus
den Ordnern unter static/css/ (generator/css.py). Hier steht nur der Ablauf.
"""

import shutil
from pathlib import Path

from generator import paths
from generator.config import SiteConfig, load_config
from generator.content import load_site
from generator.css import CSS_DIR, schreibe_stylesheets, stylesheet_ordner
from generator.paths import DIST_DIR, STATIC_DIR

# Weiterhin über generator.build erreichbar (Tests, ältere Notizen).
from generator.render import kurzbeschreibung, make_env, markdown_zu_html, write_page
from generator.seiten import alle_seiten

__all__ = ["build", "kurzbeschreibung", "make_env", "markdown_zu_html", "write_page"]


def build(output_dir: Path = DIST_DIR, config: SiteConfig | None = None) -> None:
    config = config or load_config()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    env = make_env(config)
    site_data = load_site(paths.CONTENT_DIR)
    for schreibe_seite in alle_seiten():
        schreibe_seite(env, output_dir, site_data)

    if STATIC_DIR.exists():
        # Stylesheet-Ordner (static/css/<name>/) nicht kopieren, sondern zusammenhängen.
        ordner = set(stylesheet_ordner())
        shutil.copytree(
            STATIC_DIR,
            output_dir / "static",
            ignore=lambda d, namen: [n for n in namen if Path(d, n) in ordner],
        )
        schreibe_stylesheets(output_dir / "static" / "css", CSS_DIR)
