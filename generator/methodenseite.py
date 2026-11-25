"""Methodenseiten /methoden/<id>/ (PRD 5.3, DESIGN.md › Methodenseite)."""

import html
import re
from dataclasses import dataclass
from pathlib import Path

import markdown
from jinja2 import Environment
from markupsafe import Markup

from generator.content import Methode, SiteData
from generator.render import write_page

NUTZEN_MAX = 160


def nutzen_satz(methode: Methode) -> str:
    """Ein Satz Nutzen: Feld `kurz`, sonst der erste Ablaufschritt (gekürzt)."""
    if methode.kurz:
        return methode.kurz
    treffer = re.search(r"^\s*1\.\s+(.+)$", methode.body, re.M)
    if not treffer:
        return ""
    text = _als_text(treffer.group(1))
    if len(text) <= NUTZEN_MAX:
        return text
    return text[: NUTZEN_MAX - 1].rsplit(" ", 1)[0] + " …"


def _als_text(markdown_text: str) -> str:
    """Inline-Markdown ohne Auszeichnung als Klartext."""
    gerendert = markdown.markdown(markdown_text)
    return html.unescape(re.sub(r"<[^>]+>", "", gerendert)).strip()


@dataclass
class Abschnitt:
    """Ein Teil der Anleitung: `## Überschrift` + Inhalt als HTML."""

    titel: str
    slug: str
    html: Markup
    zettel: bool  # Tipps/Varianten: als Zettel/Karte neben- statt untereinander


def anleitung(methode: Methode) -> list[Abschnitt]:
    """Teilt den Markdown-Body an den `## `-Überschriften.

    Der Ablauf (bzw. der erste Abschnitt) ist der Hauptteil; Text vor der ersten
    Überschrift steht als Einleitung darin vor den Schritten. Alle übrigen
    Abschnitte (Tipps, Varianten …) werden Zettel.
    """
    teile = re.split(r"^##[ \t]+(.+?)[ \t]*$", methode.body, flags=re.M)
    einleitung, rest = teile[0].strip(), teile[1:]
    roh = [(titel.strip(), text.strip()) for titel, text in zip(rest[::2], rest[1::2], strict=True)]
    if not roh:
        roh = [("Anleitung", "")]
    haupt = next((i for i, (titel, _) in enumerate(roh) if _slug(titel) == "ablauf"), 0)
    abschnitte = [
        Abschnitt(titel, _slug(titel), _html(text), zettel=i != haupt)
        for i, (titel, text) in enumerate(roh)
    ]
    # Einleitung getrennt rendern: sonst verschmilzt Python-Markdown eine Liste darin
    # mit der nummerierten Schrittliste.
    abschnitte[haupt].html = _html(einleitung) + abschnitte[haupt].html
    return abschnitte


def _html(markdown_text: str) -> Markup:
    return Markup(markdown.markdown(markdown_text))


def _slug(text: str) -> str:
    text = text.lower().translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def kurzinfos(methode: Methode, daten: SiteData) -> list[tuple[str, str]]:
    """Kurzinfos für den Kopf; Werte-Labels kommen aus filter.yaml."""
    labels = {(g.feld, w.id): w.label for g in daten.filter for w in g.werte}

    def liste(feld: str) -> str:
        return ", ".join(labels.get((feld, wert), wert) for wert in getattr(methode, feld))

    return [
        ("Dauer", methode.dauer),
        ("Wann", liste("zeitpunkt")),
        ("Form", liste("form")),
        ("Richtung", liste("richtung")),
        ("Material", methode.material),
    ]


def render(env: Environment, output_dir: Path, daten: SiteData) -> None:
    kategorien = {k.id: k for k in daten.kategorien}
    for methode in daten.methoden:
        write_page(
            env,
            output_dir,
            f"methoden/{methode.id}",
            "methode.html",
            aktiver_bereich="methoden",
            methode=methode,
            kategorie=kategorien[methode.kategorie],
            nutzen=nutzen_satz(methode),
            kurzinfos=kurzinfos(methode, daten),
            anleitung=anleitung(methode),
        )
