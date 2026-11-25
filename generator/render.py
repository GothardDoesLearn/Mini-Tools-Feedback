"""Jinja-Umgebung und Seitenausgabe – gemeinsam für alle Seitentypen."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from generator.config import SiteConfig
from generator.content import SiteData
from generator.paths import TEMPLATES_DIR


def make_env(config: SiteConfig, daten: SiteData | None = None) -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["site"] = config
    if daten is not None:
        env.globals["inhalte"] = daten
    return env


def write_page(env: Environment, output_dir: Path, url_path: str, template: str, **context):
    """Rendert `template` nach `output_dir/url_path/index.html` (url_path "" = Startseite)."""
    target = output_dir / url_path / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(env.get_template(template).render(**context), encoding="utf-8")
