"""Seiten-Register: jede Seite (oder Seitengruppe) meldet sich selbst mit `@seite` an.

Neue Seite = neue Datei `generator/seiten/<name>.py` mit einer Funktion

    from generator.seiten import seite
    from generator.render import write_page

    @seite
    def meine_seite(env, output_dir, site):
        write_page(env, output_dir, "pfad", "template.html", ...)

`build()` ruft `alle_seiten()` auf: Das importiert alle Module dieses Pakets (alphabetisch)
und liefert die angemeldeten Funktionen in dieser Reihenfolge. Eine zentrale Liste gibt es
nicht – beim Hinzufügen einer Seite wird keine gemeinsame Datei angefasst.
"""

import importlib
import pkgutil
from collections.abc import Callable
from pathlib import Path

from jinja2 import Environment

from generator.content import SiteData

Seite = Callable[[Environment, Path, SiteData], None]

_SEITEN: list[Seite] = []


def seite(funktion: Seite) -> Seite:
    """Dekorator: meldet `funktion(env, output_dir, site)` beim Build an."""
    _SEITEN.append(funktion)
    return funktion


def alle_seiten() -> list[Seite]:
    """Alle angemeldeten Seiten-Funktionen, sortiert nach Modul- und Funktionsname."""
    for modul in sorted(m.name for m in pkgutil.iter_modules(__path__)):
        importlib.import_module(f"{__name__}.{modul}")
    return sorted(_SEITEN, key=lambda f: (f.__module__, f.__name__))
