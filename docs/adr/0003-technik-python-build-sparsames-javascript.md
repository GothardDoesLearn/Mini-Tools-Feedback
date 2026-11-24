# Technik: Python-Build, plain CSS, sparsames JavaScript

Die Website ist eine statische Seite, die der Betreiber privat pflegt. Er kennt Python, aber kein JavaScript/TypeScript, und will die Seite langfristig selbst verstehen und warten können. Deshalb erzeugt ein eigenes, schlankes Python-Build-Skript die Seite: Es liest `content/` (Markdown mit YAML-Frontmatter und YAML-Stammdaten), prüft die Inhalte mit **Pydantic** und rendert HTML mit **Jinja2**-Vorlagen nach `dist/`. Markdown wird mit **python-markdown**, YAML mit **PyYAML** gelesen. Gestaltung mit **plain CSS** und CSS-Variablen.

JavaScript wird **sparsam** eingesetzt: nur dort, wo es einen klaren Mehrwert bringt und HTML/CSS dasselbe nicht ebenso gut können. Einfaches JavaScript ohne TypeScript, ohne Framework, ohne Bibliotheken und ohne eigenen Build-Schritt. Eingesetzt für:

- Filter, Trefferzahl, Volltextsuche (Index als JSON, beim Build von Python erzeugt), Dauer-Regler
- Filter und Suche in der URL (teilbare Links), Button „Zufällige Methode“
- Ansichts-Umschalter mit Speicherung der Wahl
- Zwei-Klick-Einbettung von Videos
- Button „Drucken“ auf Druckvorlagen

Alles andere (Seitenaufbau, Navigation, Methoden-, Kategorie-, Tool- und Vorlagenseiten, Druck) ist reines HTML/CSS. Ohne JavaScript bleiben alle Inhalte erreichbar: Die Übersicht zeigt alle Karten, die Ansicht ist Pinnwand, Videos sind als Link erreichbar, gedruckt wird über den Browser.

Werkzeuge:

- Python ≥ 3.12; Abhängigkeiten mit festen Versionen in `requirements.txt`, Entwicklungswerkzeuge in `requirements-dev.txt`, Installation in eine virtuelle Umgebung (`.venv`).
- Befehle: `python build.py` (Build nach `dist/`), `python build.py --check` (nur Inhalte prüfen), `python build.py --serve` (lokale Vorschau, baut bei Änderungen neu).
- Tests mit **pytest** (Inhaltsprüfung, Querverweise, Build läuft durch); Formatierung und Lint mit **ruff**.

## Considered Options

- Astro (Node.js, TypeScript): verworfen. Gleiches Ergebnis für Besucher, aber hunderte npm-Abhängigkeiten, häufige Hauptversionen mit inkompatiblen Änderungen und eine Sprache, die der Betreiber nicht pflegen kann. Die meisten Astro-Funktionen (Bildoptimierung, Integrationen) braucht die Seite nicht.
- Fertige Python-Generatoren (Pelican, MkDocs): verworfen, weil sie auf Blogs bzw. technische Dokumentation zugeschnitten sind und zwei Ansichten, Filter und Druckvorlagen schlecht abbilden.
- Filter rein per CSS (`:has()`), damit sie ohne JavaScript laufen: verworfen. Die nötigen, aus `filter.yaml` erzeugten Selektoren wären schwer zu lesen; Suche und teilbare Links brauchen ohnehin JavaScript, sodass ein gemeinsames kleines Skript einfacher zu warten ist.

## Consequences

- Das Build-Skript ist eigener Code: Fehler beheben wir selbst. Es bleibt klein und wird durch Schema-Prüfung und Tests abgesichert.
- Ohne JavaScript funktionieren Filter und Suche nicht; alle Inhalte bleiben aber erreichbar.
- Ersetzt die Technik-Angaben in PRD §4 (Astro, Zod, TypeScript).
