"""Prüft Konfiguration und Inhalte, ohne etwas zu schreiben.

Spätere Issues ergänzen hier Content-Schema und Querverweise. Fehler werden als
Exception gemeldet; build.py --check und der Build brechen dann ab.
"""

from generator.config import SiteConfig, load_config


def check() -> SiteConfig:
    return load_config()
