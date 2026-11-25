"""Hilfen für Druckvorlagen-Layouts (templates/vorlagen/): Texte aus der Methode statt Kopien."""

import re

from generator.content import ContentError, Methode

# Ablaufschritt der Form: 1. **Titel:** „Satzanfang“ (Hinweis)
_SATZANFANG = re.compile(r"^\d+\.\s+\*\*(.+?):\*\*\s+„(.+?)“(?:\s+\((.+?)\))?\s*$", re.M)


def satzanfaenge(methode: Methode) -> list[tuple[str, str, str | None]]:
    """Satzanfänge (Titel, Satz, Hinweis oder None) aus den Ablaufschritten der Methode."""
    treffer = [(t, s, h or None) for t, s, h in _SATZANFANG.findall(methode.body)]
    if not treffer:
        raise ContentError(
            f"{methode.id}.md: keine Satzanfänge im Ablauf gefunden "
            "(erwartet: 1. **Titel:** „Satzanfang“ (Hinweis))."
        )
    return treffer
