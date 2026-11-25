"""Methodenkarten für Übersichten (Startseite, Kategorieseiten): Anzeigedaten und Sortierung."""

import re
from dataclasses import dataclass, field

from generator.content import Kategorie, Methode, SiteData

KURZTEXT_MAX_ZEICHEN = 110
_UMLAUTE = str.maketrans({"ä": "a", "ö": "o", "ü": "u", "ß": "ss"})


@dataclass(frozen=True)
class Karte:
    id: str
    titel: str
    kurz: str
    dauer: str
    kategorie: Kategorie
    formen: list[tuple[str, str]]  # (id, label) aus filter.yaml
    druckvorlage: bool
    druckvorlage_optional: bool
    status: str
    # Filterwerte je Feld aus filter.yaml (Issue #14), z. B. {"zeitpunkt": ["stundenende"]}
    filterwerte: dict[str, list[str]] = field(default_factory=dict)

    @property
    def url(self) -> str:
        return f"/methoden/{self.id}/"


def titel_sortierschluessel(titel: str) -> str:
    """Alphabetisch nach DIN 5007-1 (ä wie a usw.), ohne Groß-/Kleinschreibung."""
    return titel.casefold().translate(_UMLAUTE)


def kurztext(methode: Methode, max_zeichen: int = KURZTEXT_MAX_ZEICHEN) -> str:
    """Feld `kurz`; fehlt es, der erste Ablaufschritt, an einer Wortgrenze gekürzt (PRD §6)."""
    if methode.kurz:
        return methode.kurz
    schritt = re.search(r"^## Ablauf\s*\n+\s*1\.\s+(.+)$", methode.body, re.M)
    if not schritt:
        return ""
    text = re.sub(r"[*_`]", "", schritt.group(1)).strip()
    if len(text) <= max_zeichen:
        return text
    return text[:max_zeichen].rsplit(" ", 1)[0].rstrip(" ,;:–-") + " …"


def hat_druckvorlage(methode: Methode, site: SiteData) -> bool:
    """Mindestens eine Druckvorlage, die nicht im Status `platzhalter` ist (PRD §9.3).
    Gilt für Karten-Icon und Filter gleichermaßen."""
    vorlagen_status = {v.id: v.status for v in site.druckvorlagen}
    return any(vorlagen_status[v] != "platzhalter" for v in methode.druckvorlagen)


def filterwerte(methode: Methode, site: SiteData) -> dict[str, list[str]]:
    """Werte je Filtergruppe (Reihenfolge wie filter.yaml). `druckvorlage` ist abgeleitet:
    "ja", wenn mindestens eine Druckvorlage nicht im Status `platzhalter` ist (PRD §9.3)."""
    werte = {}
    for gruppe in site.filter:
        if gruppe.feld == "druckvorlage":
            werte["druckvorlage"] = ["ja" if hat_druckvorlage(methode, site) else "nein"]
        else:
            wert = getattr(methode, gruppe.feld)
            werte[gruppe.feld] = list(wert) if isinstance(wert, list) else [wert]
    return werte


def karten(site: SiteData) -> list[Karte]:
    """Alle Methoden als Karten, nach Kategorie (Reihenfolge in kategorien.yaml), dann Titel."""
    kategorien = {k.id: k for k in site.kategorien}
    reihenfolge = {k.id: i for i, k in enumerate(site.kategorien)}
    form_labels = {
        w.id: w.label for gruppe in site.filter if gruppe.feld == "form" for w in gruppe.werte
    }
    methoden = sorted(
        site.methoden,
        key=lambda m: (reihenfolge[m.kategorie], titel_sortierschluessel(m.titel)),
    )
    return [
        Karte(
            id=m.id,
            titel=m.titel,
            kurz=kurztext(m),
            dauer=m.dauer,
            kategorie=kategorien[m.kategorie],
            formen=[(f, form_labels.get(f, f)) for f in m.form],
            druckvorlage=hat_druckvorlage(m, site),
            druckvorlage_optional=m.druckvorlage_optional,
            status=m.status,
            filterwerte=filterwerte(m, site),
        )
        for m in methoden
    ]
