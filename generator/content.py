"""Lädt die Methoden aus content/methoden/ und prüft sie gegen das Schema (PRD §6).

Erlaubte Werte für kategorie, richtung, zeitpunkt und form kommen aus den
Stammdaten (kategorien.yaml, filter.yaml), nicht aus dem Code.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from generator.paths import CONTENT_DIR

# Bearbeitungsstand einer Methode oder Druckvorlage (PRD §6); Textseiten haben eigene Stufen.
Status = Literal["fertig", "annahme", "platzhalter"]
SeitenStatus = Literal["fertig", "entwurf", "platzhalter"]
PLATZHALTER: Status = "platzhalter"


_UMLAUTE = str.maketrans({"ä": "a", "ö": "o", "ü": "u", "ß": "ss"})


def titel_sortierschluessel(titel: str) -> str:
    """Alphabetisch nach DIN 5007-1 (ä wie a usw.), ohne Groß-/Kleinschreibung."""
    return titel.casefold().translate(_UMLAUTE)


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
    status: Status
    hinweis: str | None = None
    verwandt: list[str] = []
    videos: list[Video] = []
    body: str


class Kategorie(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    slug: str
    titel: str
    kurz: str
    beschreibung: str
    farbe: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    kurzname: str
    papier: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    pin: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")

    @property
    def url(self) -> str:
        return f"/kategorien/{self.slug}/"


class FilterWert(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    erklaerung: str | None = None


class FilterGruppe(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feld: str
    titel: str
    quelle: str | None = None
    abgeleitet: str | None = None
    werte: list[FilterWert] = []


class Tool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    titel: str
    url: str
    zweck: str
    ablauf: str
    sus_geraete: str
    hinweis: str | None = None
    methoden: list[str] = []


class ToolsDatei(BaseModel):
    """content/tools.yaml: allgemeiner Freigabe-Hinweis und die Tools."""

    model_config = ConfigDict(extra="forbid")

    hinweis_freigabe: str = Field(min_length=1)
    tools: list[Tool]


class Druckvorlage(BaseModel):
    """Eine Zeile der Vorlagen-Tabelle aus docs/DRUCKVORLAGEN.md.

    Die zugehörigen Methoden stehen nur in deren Feld `druckvorlagen`
    (SiteData.methoden_mit_vorlage, PRD §9.6)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    titel: str
    inhalt: str
    seiten: str
    status: Status


class StartseitenTexte(BaseModel):
    """Texte der Startseite aus content/startseite.yaml (PRD §5.1)."""

    model_config = ConfigDict(extra="forbid")

    titel: str = Field(min_length=1)
    intro: str = Field(min_length=1)


class Seite(BaseModel):
    """Eine Textseite aus content/seiten/ (z. B. Über, Impressum, Datenschutz)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    titel: str
    status: SeitenStatus
    hinweis: str | None = None
    body: str


class SiteData(BaseModel):
    """Alle Inhalte aus content/, geprüft inklusive Querverweisen."""

    kategorien: list[Kategorie]
    filter: list[FilterGruppe]
    tools: list[Tool]
    tools_hinweis: str  # hinweis_freigabe aus tools.yaml
    druckvorlagen: list[Druckvorlage]
    methoden: list[Methode]

    def kategorie(self, kategorie_id: str) -> Kategorie:
        """Die Kategorie mit dieser ID (A–G) aus kategorien.yaml."""
        return next(k for k in self.kategorien if k.id == kategorie_id)

    def methoden_mit_vorlage(self, vorlage_id: str) -> list[Methode]:
        """Methoden, die diese Druckvorlage in ihrem Feld `druckvorlagen` nennen, nach Titel."""
        return sorted(
            (m for m in self.methoden if vorlage_id in m.druckvorlagen),
            key=lambda m: titel_sortierschluessel(m.titel),
        )


ERLAUBTE_WERTE_FELDER = ("kategorie", "richtung", "zeitpunkt", "form")


def _schemafehler(dateiname: str, e: ValidationError) -> ContentError:
    details = "\n".join(
        f"  - {'.'.join(str(teil) for teil in err['loc']) or '(Datei)'}: {err['msg']}"
        for err in e.errors()
    )
    return ContentError(f"{dateiname} entspricht nicht dem Schema:\n{details}")


def _load_liste[T: BaseModel](path: Path, modell: type[T]) -> list[T]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise ContentError(f"{path.name}: kein gültiges YAML: {e}") from e
    try:
        return TypeAdapter(list[modell]).validate_python(data)
    except ValidationError as e:
        raise _schemafehler(f"{path.name}:", e) from e


def load_startseite(content_dir: Path = CONTENT_DIR) -> StartseitenTexte:
    path = content_dir / "startseite.yaml"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        raise ContentError(f"{path.name}: nicht lesbar: {e}") from e
    try:
        return StartseitenTexte.model_validate(data)
    except ValidationError as e:
        raise _schemafehler(f"{path.name}:", e) from e


def load_kategorien(content_dir: Path = CONTENT_DIR) -> list[Kategorie]:
    return _load_liste(content_dir / "kategorien.yaml", Kategorie)


def load_filter(content_dir: Path = CONTENT_DIR) -> list[FilterGruppe]:
    return _load_liste(content_dir / "filter.yaml", FilterGruppe)


def load_tools_datei(content_dir: Path = CONTENT_DIR) -> ToolsDatei:
    path = content_dir / "tools.yaml"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise ContentError(f"{path.name}: kein gültiges YAML: {e}") from e
    try:
        return ToolsDatei.model_validate(data)
    except ValidationError as e:
        raise _schemafehler(f"{path.name}:", e) from e


def load_tools(content_dir: Path = CONTENT_DIR) -> list[Tool]:
    return load_tools_datei(content_dir).tools


def load_druckvorlagen(content_dir: Path = CONTENT_DIR) -> list[Druckvorlage]:
    return _load_liste(content_dir / "druckvorlagen.yaml", Druckvorlage)


def erlaubte_werte(content_dir: Path = CONTENT_DIR) -> dict[str, list[str]]:
    """Erlaubte Werte je Feld aus kategorien.yaml und filter.yaml."""
    werte = {"kategorie": [k.id for k in load_kategorien(content_dir)]}
    for gruppe in load_filter(content_dir):
        if gruppe.feld in ERLAUBTE_WERTE_FELDER and gruppe.werte:
            werte[gruppe.feld] = [w.id for w in gruppe.werte]
    return werte


def _read_markdown_datei(path: Path) -> dict:
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
        methode = Methode.model_validate(_read_markdown_datei(path))
    except ValidationError as e:
        raise _schemafehler(f"{path.name}: Frontmatter", e) from e
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


def _load_seite(path: Path) -> Seite:
    try:
        seite = Seite.model_validate(_read_markdown_datei(path))
    except ValidationError as e:
        raise _schemafehler(f"{path.name}: Frontmatter", e) from e
    if seite.id != path.stem:
        raise ContentError(
            f"{path.name}: id '{seite.id}' muss dem Dateinamen entsprechen ('{path.stem}')."
        )
    return seite


def load_seiten(content_dir: Path = CONTENT_DIR) -> list[Seite]:
    """Lädt die Textseiten aus content/seiten/; bei Fehlern ContentError."""
    return [_load_seite(path) for path in sorted((content_dir / "seiten").glob("*.md"))]


def load_site(content_dir: Path = CONTENT_DIR) -> SiteData:
    """Lädt alle Inhalte und prüft die Querverweise; bei Fehlern ContentError.

    Die kategorie einer Methode prüft schon load_methoden.
    """
    tools_datei = load_tools_datei(content_dir)
    site = SiteData(
        kategorien=load_kategorien(content_dir),
        filter=load_filter(content_dir),
        tools=tools_datei.tools,
        tools_hinweis=tools_datei.hinweis_freigabe,
        druckvorlagen=load_druckvorlagen(content_dir),
        methoden=load_methoden(content_dir),
    )
    fehler = _pruefe_querverweise(site)
    if fehler:
        raise ContentError("\n".join(fehler))
    return site


def _unbekannt(datei: str, feld: str, ids: list[str], bekannt: set[str]) -> list[str]:
    return [f"{datei}: {feld} '{i}' ist unbekannt." for i in ids if i not in bekannt]


def _pruefe_querverweise(site: SiteData) -> list[str]:
    tool_ids = {t.id for t in site.tools}
    methoden_ids = {m.id for m in site.methoden}
    vorlagen_ids = {v.id for v in site.druckvorlagen}
    fehler = []
    for m in site.methoden:
        fehler += _unbekannt(f"{m.id}.md", "tools", m.tools, tool_ids)
        fehler += _unbekannt(f"{m.id}.md", "verwandt", m.verwandt, methoden_ids)
        fehler += _unbekannt(f"{m.id}.md", "druckvorlagen", m.druckvorlagen, vorlagen_ids)
    for t in site.tools:
        fehler += _unbekannt(f"tools.yaml: {t.id}", "methoden", t.methoden, methoden_ids)
    genutzte_vorlagen = {v for m in site.methoden for v in m.druckvorlagen}
    for v in site.druckvorlagen:
        if v.id not in genutzte_vorlagen:
            fehler.append(f"druckvorlagen.yaml: {v.id}: keine Methode nennt diese Vorlage.")
    return fehler
