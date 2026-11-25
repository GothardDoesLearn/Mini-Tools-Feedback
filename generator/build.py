"""Baut die Website: Konfiguration und Inhalte laden, Seiten rendern, statische Dateien kopieren.

Neuer Seitentyp: Modul mit `render(env, output_dir, daten)` anlegen (Vorbild
generator/methodenseite.py) und in SEITEN eintragen.
"""

import shutil
from collections.abc import Callable
from pathlib import Path

from jinja2 import Environment

from generator import methodenseite, paths
from generator.config import SiteConfig, load_config
from generator.content import SiteData, load_site
from generator.paths import DIST_DIR, STATIC_DIR
from generator.render import make_env, write_page

__all__ = ["SEITEN", "build", "make_env", "write_page"]

type Seitenrenderer = Callable[[Environment, Path, SiteData], None]


def startseite(env: Environment, output_dir: Path, daten: SiteData) -> None:
    write_page(env, output_dir, "", "index.html", aktiver_bereich="methoden")


SEITEN: list[Seitenrenderer] = [
    startseite,
    methodenseite.render,
]


def build(output_dir: Path = DIST_DIR, config: SiteConfig | None = None) -> None:
    config = config or load_config()
    daten = load_site(paths.CONTENT_DIR)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    env = make_env(config, daten)
    for render in SEITEN:
        render(env, output_dir, daten)

    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, output_dir / "static")
