"""Anzeigetexte für den Bearbeitungsstand (AGENTS.md: annahme/platzhalter sichtbar kennzeichnen).

Einzige Stelle für diese Texte; in Templates als Global `status_texte[art][status]`
(art: "methode", "vorlage", "seite"). Status ohne Eintrag (z. B. fertig) wird nicht gekennzeichnet.
"""

from typing import NamedTuple


class StatusText(NamedTuple):
    marke: str  # kurzes Etikett (Karte, Vorlagenliste, Seitenleiste)
    titel: str  # fett vor dem Hinweistext
    text: str  # Standardtext, wenn der Inhalt kein eigenes Feld `statushinweis` hat


_PLATZHALTER_TEXT = "Dieser Inhalt fehlt noch und folgt nach Rücksprache."

STATUS_TEXTE: dict[str, dict[str, StatusText]] = {
    "methode": {
        "annahme": StatusText("wird geprüft", "Wird noch geprüft", "Der Ablauf wird noch geprüft."),
        "platzhalter": StatusText("Platzhalter", "Platzhalter", _PLATZHALTER_TEXT),
    },
    "vorlage": {
        "annahme": StatusText(
            "wird geprüft",
            "Wird noch geprüft",
            "Diese Druckvorlage ist nach aktueller Spezifikation gebaut und noch nicht "
            "abschließend geprüft.",
        ),
        "platzhalter": StatusText(
            "Vorlage folgt", "Vorlage folgt", "Diese Druckvorlage ist noch nicht fertig."
        ),
    },
    "seite": {
        "platzhalter": StatusText("Platzhalter", "Platzhalter", _PLATZHALTER_TEXT),
        "entwurf": StatusText(
            "Entwurf", "Entwurf", "Dieser Text ist ein Entwurf und noch nicht freigegeben."
        ),
    },
}
