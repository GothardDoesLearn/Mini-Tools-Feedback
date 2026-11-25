"""Methodenseiten /methoden/<id>/ (PRD 5.3, DESIGN.md › Methodenseite)."""

import re
from dataclasses import dataclass

import markdown
from markupsafe import Markup

from generator.content import Methode, SiteData, Tool
from generator.karten import kurztext, titel_sortierschluessel
from generator.video import anzeige

NUTZEN_MAX = 160  # Satz Nutzen im Kopf: Feld `kurz`, sonst 1. Ablaufschritt gekürzt


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


def kontext(methode: Methode, daten: SiteData) -> dict:
    """Render-Kontext für templates/methode.html (geschrieben von seiten/methodenseiten.py)."""
    kategorie = daten.kategorie(methode.kategorie)
    nutzen = kurztext(methode, NUTZEN_MAX)
    return {
        "aktiver_bereich": "methoden",
        "seitentitel": methode.titel,
        "beschreibung": f"{methode.titel}: {nutzen}" if nutzen else methode.titel,
        "methode": methode,
        "kategorie": kategorie,
        "nutzen": nutzen,
        "kurzinfos": kurzinfos(methode, daten),
        "anleitung": anleitung(methode),
        # Rechte Spalte (Issue #8, templates/methode_seitenleiste.html)
        "druckvorlagen": [
            v for i in methode.druckvorlagen for v in daten.druckvorlagen if v.id == i
        ],
        "ist_digital": ist_digital(methode),
        "digitale_tools": digitale_tools(methode, daten),
        "tools_hinweis": daten.tools_hinweis,
        "passt_auch_dazu": [
            (m, daten.kategorie(m.kategorie)) for m in passt_auch_dazu(methode, daten)
        ],
        "videos": [anzeige(v) for v in methode.videos],
    }


PASST_AUCH_DAZU_MAX = 3


def passt_auch_dazu(methode: Methode, daten: SiteData) -> list[Methode]:
    """Zuerst `verwandt`, aufgefüllt mit der gleichen Kategorie (nach Titel), max. 3."""
    nach_id = {m.id: m for m in daten.methoden}
    gleiche_kategorie = sorted(
        (m for m in daten.methoden if m.kategorie == methode.kategorie),
        key=lambda m: titel_sortierschluessel(m.titel),
    )
    vorschlaege: list[Methode] = []
    for kandidat in [nach_id[i] for i in methode.verwandt] + gleiche_kategorie:
        if kandidat.id != methode.id and kandidat not in vorschlaege:
            vorschlaege.append(kandidat)
    return vorschlaege[:PASST_AUCH_DAZU_MAX]


def ist_digital(methode: Methode) -> bool:
    return "digital" in methode.form


def digitale_tools(methode: Methode, daten: SiteData) -> list[Tool]:
    """Nur bei digitalen Methoden (PRD §5.3): Tools aus dem Feld `tools` der Methode, dazu
    Tools, die die Methode in tools.yaml nennen."""
    if not ist_digital(methode):
        return []
    ids = list(methode.tools)
    ids += [t.id for t in daten.tools if methode.id in t.methoden and t.id not in ids]
    nach_id = {t.id: t for t in daten.tools}
    return [nach_id[i] for i in ids]
