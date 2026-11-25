"""Baut die Website: Konfiguration laden, Seiten rendern, statische Dateien kopieren."""

import re
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from generator.config import SiteConfig, load_config
from generator.paths import DIST_DIR, STATIC_DIR, TEMPLATES_DIR


def kurzbeschreibung(text: str, max_laenge: int = 160) -> str:
    """Macht aus Markdown-Text eine einzeilige Meta-Description, gekürzt an einer Wortgrenze."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)  # Links/Bilder -> Linktext
    text = re.sub(r"[*_`#>]+", "", text)
    text = " ".join(text.split())
    if len(text) <= max_laenge:
        return text
    gekuerzt = text[: max_laenge - 1]
    if text[max_laenge - 1] != " ":
        gekuerzt = gekuerzt.rsplit(" ", 1)[0]
    return gekuerzt.rstrip(" ,;:.–-") + "…"


def make_env(config: SiteConfig) -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["site"] = config
    env.filters["kurzbeschreibung"] = kurzbeschreibung
    return env


def write_page(env: Environment, output_dir: Path, url_path: str, template: str, **context):
    """Rendert `template` nach `output_dir/url_path/index.html` (url_path "" = Startseite).

    Seitenkopf über den Kontext: `seitentitel` (-> "<seitentitel> – <Website-Name>", leer =
    nur Website-Name) und `beschreibung` (Meta-Description, Standard: `site.beschreibung`;
    aus Inhalten z. B. `methode.kurz` oder `text | kurzbeschreibung`). Beides muss je Seite
    eindeutig sein (tests/test_seitenkopf.py).
    """
    target = output_dir / url_path / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(env.get_template(template).render(**context), encoding="utf-8")


def build(output_dir: Path = DIST_DIR, config: SiteConfig | None = None) -> None:
    config = config or load_config()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    env = make_env(config)
    write_page(env, output_dir, "", "index.html", aktiver_bereich="methoden")
    (output_dir / "404.html").write_text(env.get_template("404.html").render(), encoding="utf-8")

    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, output_dir / "static")
