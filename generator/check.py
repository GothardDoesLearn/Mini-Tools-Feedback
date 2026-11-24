"""Prüft Konfiguration und Inhalte, ohne etwas zu schreiben.

Fehler werden als Exception gemeldet (Inhalte: ContentError); build.py --check und
der Build brechen dann ab. Spätere Issues ergänzen hier die Querverweise.
"""

from generator import paths
from generator.config import SiteConfig, load_config
from generator.content import load_methoden


def check() -> SiteConfig:
    config = load_config()
    load_methoden(paths.CONTENT_DIR)
    return config
