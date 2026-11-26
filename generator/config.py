"""Lädt und prüft die zentrale Konfiguration (config.yaml)."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from generator.paths import CONFIG_FILE


class SiteConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    website_name: str
    # Optional: leer = keine Domain im Fußtext der Druckvorlagen. Nur Schema + Host, kein Pfad,
    # weil die Website im Wurzelverzeichnis liegen muss (docs/DEPLOYMENT.md).
    domain: str = Field(default="", pattern=r"^(https?://[^/\s]+/?)?$")
    beschreibung: str
    # Hinweise (PRD §5.8): Repository für „Auf GitHub melden“, Adresse für „Per E-Mail schreiben“
    github_repo: str
    kontakt_email: str
    werbung_aktiv: bool = False
    # Übersicht: Werbeplatz nach jeder n-ten Methodenkarte (nur wirksam, wenn werbung_aktiv).
    werbung_nach_karten: int = Field(default=6, ge=1)

    @property
    def domain_anzeige(self) -> str:
        """Domain ohne Schema und Schrägstrich (Fußtext der Druckvorlagen); leer ohne Domain."""
        return self.domain.split("://", 1)[-1].rstrip("/")


def load_config(path: Path = CONFIG_FILE) -> SiteConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return SiteConfig.model_validate(data)
