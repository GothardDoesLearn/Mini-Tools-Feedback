"""Baut die Website: Konfiguration laden, Seiten rendern, statische Dateien kopieren."""

import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from generator import paths
from generator.config import SiteConfig, load_config
from generator.content import load_site
from generator.karten import karten
from generator.paths import DIST_DIR, STATIC_DIR, TEMPLATES_DIR


def make_env(config: SiteConfig) -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["site"] = config
    return env


def write_page(env: Environment, output_dir: Path, url_path: str, template: str, **context):
    """Rendert `template` nach `output_dir/url_path/index.html` (url_path "" = Startseite)."""
    target = output_dir / url_path / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(env.get_template(template).render(**context), encoding="utf-8")


def build(output_dir: Path = DIST_DIR, config: SiteConfig | None = None) -> None:
    config = config or load_config()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    env = make_env(config)
    site_daten = load_site(paths.CONTENT_DIR)
    write_page(
        env, output_dir, "", "index.html", aktiver_bereich="methoden", karten=karten(site_daten)
    )

    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, output_dir / "static")
