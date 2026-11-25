"""Daten für die Startseite: Kategorie-Auswahl mit Anzahl je Kategorie (Issue #11)."""

from collections import Counter
from dataclasses import dataclass

from generator.content import SiteData

# Eintrag „Alle“ (DESIGN.md › Kategorie-Auswahl; Farben aus docs/design/startseite-referenz).
ALLE_KURZNAME = "Alle"
ALLE_FARBEN = {"farbe": "#8A939E", "papier": "#FFFFFF", "pin": "#8A8A8A"}


@dataclass(frozen=True)
class KategorieEintrag:
    id: str  # "" = „Alle“
    kurzname: str
    anzahl: int
    farbe: str
    papier: str
    pin: str


def kategorie_auswahl(site: SiteData) -> list[KategorieEintrag]:
    """„Alle“ und jede Kategorie (Reihenfolge aus kategorien.yaml) mit Anzahl ihrer Methoden."""
    anzahl = Counter(m.kategorie for m in site.methoden)
    alle = KategorieEintrag("", ALLE_KURZNAME, len(site.methoden), **ALLE_FARBEN)
    return [alle] + [
        KategorieEintrag(k.id, k.kurzname, anzahl[k.id], k.farbe, k.papier, k.pin)
        for k in site.kategorien
    ]
