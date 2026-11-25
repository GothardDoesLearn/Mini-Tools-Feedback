"""Stylesheets aus Komponenten-Dateien zusammenhängen.

Jeder Ordner `static/css/<name>/` wird in Dateinamen-Reihenfolge zu `static/css/<name>.css`
zusammengehängt (z. B. `site/` -> `site.css`, `druckvorlage/` -> `druckvorlage.css`). Die
Nummer vorn im Dateinamen (`30-filterleiste.css`) bestimmt also die Kaskaden-Reihenfolge.
Templates binden weiter nur die zusammengehängte Datei ein.
"""

from pathlib import Path

from generator.paths import STATIC_DIR

CSS_DIR = STATIC_DIR / "css"


def stylesheet_ordner(css_dir: Path = CSS_DIR) -> list[Path]:
    """Alle Ordner, aus denen je ein Stylesheet entsteht."""
    return sorted(p for p in css_dir.iterdir() if p.is_dir()) if css_dir.is_dir() else []


def stylesheet(name: str, css_dir: Path = CSS_DIR) -> str:
    """Das zusammengehängte Stylesheet `<name>.css` als Text (auch für Tests)."""
    return stylesheet_bytes(css_dir / name).decode("utf-8").replace("\r\n", "\n")


def stylesheet_bytes(ordner: Path) -> bytes:
    # Bytes unverändert aneinander: Leerzeilen am Dateiende trennen die Abschnitte.
    return b"".join(f.read_bytes() for f in sorted(ordner.glob("*.css")))


def schreibe_stylesheets(ziel_css_dir: Path, css_dir: Path = CSS_DIR) -> None:
    """Schreibt `<ziel_css_dir>/<name>.css` für jeden Ordner unter `css_dir`."""
    ziel_css_dir.mkdir(parents=True, exist_ok=True)
    for ordner in stylesheet_ordner(css_dir):
        (ziel_css_dir / f"{ordner.name}.css").write_bytes(stylesheet_bytes(ordner))
