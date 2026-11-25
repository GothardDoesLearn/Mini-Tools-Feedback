"""Prüft Konfiguration und Inhalte, ohne etwas zu schreiben.

Fehler werden als Exception gemeldet (Inhalte: ContentError); build.py --check und
der Build brechen dann ab. Schema und Querverweise prüft generator.content.load_site.
"""

from generator import paths
from generator.config import SiteConfig, load_config
from generator.content import load_site, load_startseite


def check() -> SiteConfig:
    config = load_config()
    load_site(paths.CONTENT_DIR)
    load_startseite(paths.CONTENT_DIR)
    return config
