"""Lädt und prüft die zentrale Konfiguration (config.yaml)."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

from generator.paths import CONFIG_FILE


class SiteConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    website_name: str
    domain: str
    beschreibung: str
    werbung_aktiv: bool = False


def load_config(path: Path = CONFIG_FILE) -> SiteConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return SiteConfig.model_validate(data)
