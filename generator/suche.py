"""Suchindex für die Volltextsuche (Issue #18).

Der Build erzeugt je Methode Titel, Aliase und die Anleitung als Klartext; die Startseite bettet
die Liste als JSON ein (``<script type="application/json" data-suchindex>``), static/js/filter.js
durchsucht sie ohne externe Bibliothek (ADR 0003).
"""

import html
import re

import markdown

from generator.content import SiteData


def klartext(markdown_text: str) -> str:
    """Markdown -> einzeiliger Klartext ohne HTML-Tags."""
    ohne_tags = re.sub(r"<[^>]+>", " ", markdown.markdown(markdown_text))
    return " ".join(html.unescape(ohne_tags).split())


def suchindex(site: SiteData) -> list[dict]:
    return [
        {"id": m.id, "titel": m.titel, "aliase": m.aliase, "text": klartext(m.body)}
        for m in site.methoden
    ]
