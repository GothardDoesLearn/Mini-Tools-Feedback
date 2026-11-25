"""Methodenkarten für Übersichten (Startseite, Kategorieseiten): Anzeigedaten und Sortierung."""

import math
import re
from dataclasses import dataclass, field

from generator.content import (
    PLATZHALTER,
    Kategorie,
    Methode,
    SiteData,
    Status,
    titel_sortierschluessel,
)

KURZTEXT_MAX_ZEICHEN = 110


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
    status: Status
    # Filterwerte je Feld aus filter.yaml (Issue #14), z. B. {"zeitpunkt": ["stundenende"]}
    filterwerte: dict[str, list[str]] = field(default_factory=dict)
    # Minuten für den Dauer-Filter (Issue #19); `dauerhaft` = 0/0
    dauer_min: int | float = 0
    dauer_max: int | float = 0

    @property
    def url(self) -> str:
        return f"/methoden/{self.id}/"


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
    return any(vorlagen_status[v] != PLATZHALTER for v in methode.druckvorlagen)


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


def _minuten(wert: float) -> int | float:
    """Ganze Minuten ohne Nachkomma (für data-Attribute und Regler)."""
    return int(wert) if float(wert).is_integer() else wert


def dauer_bereich(site: SiteData) -> tuple[int, int]:
    """Spanne des Dauer-Reglers (Issue #19) in ganzen Minuten: von der kürzesten bis zur
    längsten Methode; `dauerhaft` (0/0) zählt nicht mit, solche Methoden passen immer."""
    werte = [m.dauer_max for m in site.methoden if m.dauer_max > 0] or [1]
    return max(1, math.floor(min(werte))), math.ceil(max(werte))


def karten(site: SiteData) -> list[Karte]:
    """Alle Methoden als Karten, nach Kategorie (Reihenfolge in kategorien.yaml), dann Titel."""
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
            kategorie=site.kategorie(m.kategorie),
            formen=[(f, form_labels.get(f, f)) for f in m.form],
            druckvorlage=hat_druckvorlage(m, site),
            druckvorlage_optional=m.druckvorlage_optional,
            status=m.status,
            filterwerte=filterwerte(m, site),
            dauer_min=_minuten(m.dauer_min),
            dauer_max=_minuten(m.dauer_max),
        )
        for m in methoden
    ]
