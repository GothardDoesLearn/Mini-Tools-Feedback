"""Rendern: Jinja-Umgebung, Markdown-Filter und `write_page` (von allen Seiten genutzt)."""

import re
from functools import partial
from pathlib import Path
from xml.etree.ElementTree import SubElement

import markdown
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markupsafe import Markup

from generator.config import SiteConfig
from generator.hinweis import HINWEIS_MARKE, hinweis_links
from generator.paths import TEMPLATES_DIR
from generator.status import STATUS_TEXTE
from generator.vorlagen import satzanfaenge


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


class _ExterneLinks(Treeprocessor):
    """Kennzeichnet Links nach außen wie auf der Toolseite (Klasse, rel, Screenreader-Hinweis)."""

    def run(self, root):
        for link in root.iter("a"):
            href = link.get("href", "")
            if not re.match(r"(?:https?:)?//", href):
                continue
            link.attrib.clear()
            link.set("class", "extern-link")
            link.set("href", href)
            link.set("rel", "noopener noreferrer")
            hinweis = SubElement(link, "span", {"class": "nur-screenreader"})
            hinweis.text = " (externer Link)"


class _ExterneLinksExtension(Extension):
    def extendMarkdown(self, md):  # noqa: N802 (Name von Python-Markdown vorgegeben)
        md.treeprocessors.register(_ExterneLinks(md), "externe_links", 0)


def markdown_zu_html(text: str) -> Markup:
    """Rendert Markdown aus content/ zu HTML; externe Links werden gekennzeichnet."""
    return Markup(markdown.markdown(text, extensions=[_ExterneLinksExtension()]))


def make_env(config: SiteConfig) -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["site"] = config
    env.globals["status_texte"] = STATUS_TEXTE
    env.globals["satzanfaenge"] = satzanfaenge
    env.globals["hinweis_links"] = partial(hinweis_links, config)
    env.globals["HINWEIS_MARKE"] = HINWEIS_MARKE
    env.filters["kurzbeschreibung"] = kurzbeschreibung
    env.filters["markdown"] = markdown_zu_html
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
