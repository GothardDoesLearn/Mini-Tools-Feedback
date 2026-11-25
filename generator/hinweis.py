"""Hinweis-Links: „Auf GitHub melden“ und „Per E-Mail schreiben“ (PRD §5.8, Issue #59).

Die Website verlinkt nur; vor dem Klick wird nichts von GitHub geladen (ADR 0001).
Im Template: `hinweis_links(hinweise, art, titel, id)` (Global aus generator/render.py),
gerendert von `templates/_hinweis.html`.
"""

from dataclasses import dataclass
from typing import Literal
from urllib.parse import quote, urlencode

from markupsafe import Markup

from generator.config import SiteConfig
from generator.content import HinweisTexte

# Dateiname in .github/ISSUE_TEMPLATE/ und ID des Felds „Bezug“ darin
ISSUE_VORLAGE = "hinweis.yml"
BEZUG_FELD = "bezug"

# Steht diese Zeile in einer Textseite (content/seiten/*.md), erscheinen dort die Hinweis-Links.
HINWEIS_MARKE = "<!-- hinweis-links -->"

Art = Literal["methode", "vorlage", "allgemein"]


@dataclass(frozen=True)
class HinweisLinks:
    texte: HinweisTexte
    github: str
    mailto: Markup  # als HTML-Zeichenreferenzen, direkt in href="…" einsetzen


def github_url(repo: str, titel: str, bezug: str = "") -> str:
    """Link auf das Issue-Formular mit vorausgefülltem Titel und Bezug."""
    parameter = {"template": ISSUE_VORLAGE, "title": titel}
    if bezug:
        parameter[BEZUG_FELD] = bezug
    return f"{repo.rstrip('/')}/issues/new?{urlencode(parameter, quote_via=quote)}"


def mailto(email: str, betreff: str) -> str:
    return f"mailto:{email}?subject={quote(betreff)}"


def zeichenreferenzen(text: str) -> Markup:
    """Jedes Zeichen als &#NN; – die Adresse steht so nicht im Klartext im Quelltext."""
    return Markup("".join(f"&#{ord(z)};" for z in text))


def hinweis_links(
    config: SiteConfig, texte: HinweisTexte, art: Art = "allgemein", titel: str = "", id: str = ""
) -> HinweisLinks:
    titel_text, bezug = getattr(texte, art).fuellen(titel=titel, id=id)
    return HinweisLinks(
        texte=texte,
        github=github_url(config.github_repo, titel_text, bezug),
        mailto=zeichenreferenzen(mailto(config.kontakt_email, titel_text)),
    )
