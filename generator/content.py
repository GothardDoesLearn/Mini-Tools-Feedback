"""Lädt die Methoden aus content/methoden/ und prüft sie gegen das Schema (PRD §6).

Erlaubte Werte für kategorie, richtung, zeitpunkt und form kommen aus den
Stammdaten (kategorien.yaml, filter.yaml), nicht aus dem Code.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from generator.paths import CONTENT_DIR


class ContentError(Exception):
    """Fehler in einer Datei unter content/ – der Build bricht ab."""


class Video(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titel: str
    url: str


class Methode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    titel: str
    aliase: list[str] = []
    kategorie: str
    richtung: list[str] = Field(min_length=1)
    zeitpunkt: list[str] = Field(min_length=1)
    form: list[str] = Field(min_length=1)
    dauer: str
    dauer_min: float = Field(ge=0)
    dauer_max: float = Field(ge=0)
    kurz: str | None = None
    material: str
    druckvorlagen: list[str]
    druckvorlage_optional: bool = False
    tools: list[str] = []
    status: Literal["fertig", "annahme", "platzhalter"]
    hinweis: str | None = None
    verwandt: list[str] = []
    videos: list[Video] = []
    body: str


ERLAUBTE_WERTE_FELDER = ("kategorie", "richtung", "zeitpunkt", "form")


def _read_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def erlaubte_werte(content_dir: Path = CONTENT_DIR) -> dict[str, list[str]]:
    """Erlaubte Werte je Feld aus kategorien.yaml und filter.yaml."""
    werte = {"kategorie": [k["id"] for k in _read_yaml(content_dir / "kategorien.yaml")]}
    for gruppe in _read_yaml(content_dir / "filter.yaml"):
        if gruppe["feld"] in ERLAUBTE_WERTE_FELDER and "werte" in gruppe:
            werte[gruppe["feld"]] = [w["id"] for w in gruppe["werte"]]
    return werte


def _read_methode(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    teile = text.split("---\n", 2)
    if len(teile) != 3 or teile[0].strip():
        raise ContentError(f"{path.name}: YAML-Frontmatter zwischen '---'-Zeilen fehlt.")
    _, frontmatter, body = teile
    try:
        data = yaml.safe_load(frontmatter) or {}
    except yaml.YAMLError as e:
        raise ContentError(f"{path.name}: Frontmatter ist kein gültiges YAML: {e}") from e
    if not isinstance(data, dict):
        raise ContentError(f"{path.name}: Frontmatter muss aus 'feld: wert'-Zeilen bestehen.")
    data["body"] = body.strip()
    return data


def _pruefe_werte(path: Path, methode: Methode, erlaubt: dict[str, list[str]]) -> list[str]:
    fehler = []
    for feld in ERLAUBTE_WERTE_FELDER:
        wert = getattr(methode, feld)
        for einzelwert in wert if isinstance(wert, list) else [wert]:
            if einzelwert not in erlaubt[feld]:
                fehler.append(
                    f"{path.name}: {feld} '{einzelwert}' ist unbekannt. "
                    f"Erlaubt: {', '.join(erlaubt[feld])}."
                )
    return fehler


def _load_methode(path: Path, erlaubt: dict[str, list[str]]) -> Methode:
    try:
        methode = Methode.model_validate(_read_methode(path))
    except ValidationError as e:
        details = "\n".join(
            f"  - {'.'.join(str(teil) for teil in err['loc']) or '(Datei)'}: {err['msg']}"
            for err in e.errors()
        )
        raise ContentError(
            f"{path.name}: Frontmatter entspricht nicht dem Schema:\n{details}"
        ) from e
    fehler = _pruefe_werte(path, methode, erlaubt)
    if methode.id != path.stem:
        fehler.append(
            f"{path.name}: id '{methode.id}' muss dem Dateinamen entsprechen ('{path.stem}')."
        )
    if fehler:
        raise ContentError("\n".join(fehler))
    return methode


def load_methoden(content_dir: Path = CONTENT_DIR) -> list[Methode]:
    """Lädt alle Methoden; bei Fehlern ContentError mit Dateiname und Ursache."""
    erlaubt = erlaubte_werte(content_dir)
    return [
        _load_methode(path, erlaubt) for path in sorted((content_dir / "methoden").glob("*.md"))
    ]
