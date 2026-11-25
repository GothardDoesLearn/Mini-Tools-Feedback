"""Baut die Website: Konfiguration laden, Seiten rendern, statische Dateien kopieren."""

import re
import shutil
from pathlib import Path
from xml.etree.ElementTree import SubElement

import markdown
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markupsafe import Markup

from generator import methodenseite, paths
from generator.config import SiteConfig, load_config
from generator.content import SiteData, load_seiten, load_site
from generator.karten import karten
from generator.paths import DIST_DIR, STATIC_DIR, TEMPLATES_DIR

# Layout einer Druckvorlage: templates/vorlagen/<id>.html (fehlt es: Seite „Vorlage folgt“).
VORLAGEN_LAYOUT_DIR = "vorlagen"

# Textseiten mit eigenem Menüpunkt in der Hauptnavigation (die übrigen nur im Fuß verlinkt).
SEITEN_MIT_MENUEPUNKT = {"ueber"}


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


def write_vorlagen(env: Environment, output_dir: Path, site: SiteData) -> None:
    """Schreibt /vorlagen/<id>/ für jede Druckvorlage."""
    methoden = {m.id: m for m in site.methoden}
    for vorlage in site.druckvorlagen:
        layout = f"{VORLAGEN_LAYOUT_DIR}/{vorlage.id}.html"
        gebaut = vorlage.status != "platzhalter" and (TEMPLATES_DIR / layout).is_file()
        write_page(
            env,
            output_dir,
            f"vorlagen/{vorlage.id}",
            "vorlage.html",
            aktiver_bereich="vorlagen",
            seitentitel=f"{vorlage.titel} – Druckvorlage",
            beschreibung=kurzbeschreibung(f"Druckvorlage {vorlage.titel}: {vorlage.inhalt}"),
            vorlage=vorlage,
            methoden=[methoden[m] for m in vorlage.methoden],
            layout=layout if gebaut else None,
        )


def write_methodenseiten(env: Environment, output_dir: Path, site: SiteData) -> None:
    """Schreibt /methoden/<id>/ für jede Methode (Issue #7; Kontext: generator/methodenseite.py)."""
    for methode in site.methoden:
        write_page(
            env,
            output_dir,
            f"methoden/{methode.id}",
            "methode.html",
            **methodenseite.kontext(methode, site),
        )


def write_toolseite(env: Environment, output_dir: Path, inhalte: SiteData) -> None:
    """Toolseite /tools/ aus tools.yaml (Issue #13)."""
    write_page(
        env,
        output_dir,
        "tools",
        "tools.html",
        aktiver_bereich="tools",
        tools=inhalte.tools,
        methoden_titel={m.id: m.titel for m in inhalte.methoden},
    )


def build(output_dir: Path = DIST_DIR, config: SiteConfig | None = None) -> None:
    config = config or load_config()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    env = make_env(config)
    site_data = load_site(paths.CONTENT_DIR)
    write_page(
        env, output_dir, "", "index.html", aktiver_bereich="methoden", karten=karten(site_data)
    )
    (output_dir / "404.html").write_text(env.get_template("404.html").render(), encoding="utf-8")

    write_methodenseiten(env, output_dir, site_data)
    write_toolseite(env, output_dir, site_data)
    write_page(
        env,
        output_dir,
        "vorlagen",
        "vorlagen.html",
        aktiver_bereich="vorlagen",
        druckvorlagen=site_data.druckvorlagen,
        methoden_titel={m.id: m.titel for m in site_data.methoden},
    )
    write_vorlagen(env, output_dir, site_data)
    for seite in load_seiten(paths.CONTENT_DIR):
        bereich = seite.id if seite.id in SEITEN_MIT_MENUEPUNKT else ""
        write_page(env, output_dir, seite.id, "seite.html", seite=seite, aktiver_bereich=bereich)

    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, output_dir / "static")
