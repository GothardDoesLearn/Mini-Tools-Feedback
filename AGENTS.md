# Feedback-Tools – Feedbackmethoden-Website

Öffentliche Website, die der Betreiber privat hostet. Sie stellt kurze Feedbackmethoden vor (1–10 Min, analog oder
digital), mit denen Lehrkräfte Rückmeldungen von Schülerinnen und Schülern (SuS) einholen. Zu Methoden mit Material
gibt es druckfertige Druckvorlagen.

Zielgruppe: Lehrkräfte aller Schulen und Fortbildende (nicht SuS). Sprache der Oberfläche: Deutsch.
Begriffe wie in `GLOSSARY.md` verwenden (Methode, Tool, Druckvorlage, Werbeplatz …).

## Wichtige Dateien

- `docs/PRD.md` – Anforderungen, Seiten, Datenmodell, Akzeptanzkriterien. **Vor jeder Arbeit lesen.**
- `docs/DESIGN.md` – verbindliches Design (zwei Ansichten: Pinnwand/Klar), Tokens, Referenz in `docs/design/`.
- `docs/DRUCKVORLAGEN.md` – Spezifikation aller Druckvorlagen.
- `docs/adr/` – grundlegende Entscheidungen (Datenschutz/Werbung, Lizenz). Nicht stillschweigend davon abweichen.
- `content/methoden/*.md` – eine Datei pro Methode (YAML-Frontmatter + Markdown-Anleitung). **Einzige Quelle der Inhalte.**
- `content/kategorien.yaml`, `content/filter.yaml`, `content/tools.yaml` – Stammdaten.

## Aufgaben und offene Fragen

- Aufgaben sind GitHub Issues (siehe unten „Agent skills“). Immer nur EIN Issue pro Sitzung bearbeiten.
- Ungeklärte Punkte nicht selbst entscheiden: als Issue mit Label `needs-triage` anlegen und bis dahin einen Platzhalter verwenden.
- Abhängigkeiten sind als GitHub-Abhängigkeiten („blocked by“) eingetragen. Nur Issues beginnen, deren Blocker alle geschlossen sind.
- Am Ende der Sitzung kurz zusammenfassen, was geändert wurde.

## Regeln

- Inhalte niemals im Code hart kodieren – alles kommt aus `content/`.
- Texte in `content/` nicht eigenmächtig umformulieren. Neue oder geänderte Texte nur als Entwurf vorschlagen; der Betreiber gibt frei.
- Methoden und Druckvorlagen mit Status `annahme` oder `platzhalter` sichtbar kennzeichnen (Hinweisbox).
- Datenschutz (solange Werbung ausgeschaltet ist): keine Tracker, keine Cookies, keine CDNs, keine Google Fonts,
  keine Anfragen an Drittserver. Schriften lokal einbinden. YouTube nur per Zwei-Klick-Einbettung.
- Werbeplätze nur über die vorbereitete Komponente; nie auf Druckvorlagen oder in der Druckansicht.
- Statische Seite ohne Server-Backend; Ausgabe muss auf jedem einfachen Webserver laufen.
- Barrierearm: semantisches HTML, Tastaturbedienung, Kontrast WCAG AA.
- Git: pro Issue ein Branch. Claude committet selbst, sobald `python build.py` und `pytest` fehlerfrei laufen. **Push und Pull
  Request nur nach ausdrücklichem OK des Betreibers.** Keine Co-Autor-Zeile.
- Token sparen: nur die Dateien lesen, die das Issue braucht.

## Befehle (gültig nach Issue #1 „Projekt aufsetzen“)

Technik siehe `docs/adr/0003-technik-python-build-sparsames-javascript.md` (Python-Build, plain CSS, sparsames JavaScript).

- `python -m venv .venv` und `pip install -r requirements.txt -r requirements-dev.txt` – Umgebung und Abhängigkeiten
- `python build.py --serve` – lokale Vorschau, baut bei Änderungen neu
- `python build.py` – statischer Build nach `dist/`
- `python build.py --check` – nur Content-Schema und Querverweise prüfen
- `pytest` – Tests; `ruff check` und `ruff format` – Lint und Formatierung
- `python tools/druck_pruefen.py <vorlage-id …> | --alle` – Druckvorlagen per Headless-Edge/Chrome als PDF drucken, Seitenzahl/Ausrichtung gegen `druckvorlagen.yaml` prüfen; `--screenshot /pfad/ --breite 375 --ansicht klar --out DIR` für Bildschirmfotos

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues for `GothardDoesLearn/Mini-Tools-Feedback` (via the `gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
