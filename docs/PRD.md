# PRD – Feedback-Tools-Website

Stand: 2026-11-25 · Betreiber: Daniel Handrik (Lehrkraft), privat

## 1. Ziel

Lehrkräfte finden in unter einer Minute eine passende Feedbackmethode für ihre Stunde, verstehen den
Ablauf ohne Vorwissen und können benötigtes Material sofort drucken.

## 2. Ausgangslage

Feedback-Tools ist eine **öffentliche Website**, die der Betreiber privat hostet und betreibt – kein Angebot einer
Schule. Sie richtet sich an Lehrkräfte aller Schulen. Eine spätere Finanzierung über Werbung soll möglich bleiben
(siehe `docs/adr/0001-keine-drittanfragen-ohne-einwilligung.md`).

Die Methoden stammen aus einer Fortbildung / Sammlung des Kollegiums (Pinnwände "Mini Tools").
Nach dem Zusammenführen von Dopplungen: 31 Methoden in 7 Kategorien (A–G) plus 5 digitale Tools (H).
Alle Inhalte liegen fertig in `content/`.

## 3. Nutzer & Nutzungssituation

- Lehrkräfte aller Schulen sowie Fortbildende (im Folgenden zusammen „Lehrkräfte“), oft am Handy zwischen zwei Stunden oder am PC bei der Vorbereitung.
- Wenig Zeit → schnelle Filter, kurze Anleitungen, Druck mit einem Klick.
- Teils wenig technikaffin → keine Anmeldung, keine Installation.

## 4. Technik (Entscheidung, siehe `docs/adr/0003-technik-python-build-sparsames-javascript.md`)

- **Eigenes Python-Build-Skript** (Jinja2-Vorlagen, Pydantic-Schema, python-markdown, PyYAML) erzeugt aus `content/`
  reines HTML nach `dist/`. Inhalte bleiben als Markdown editierbar, der Build bricht bei Schemafehlern ab.
- JavaScript sparsam: einfaches JavaScript ohne TypeScript, Framework oder Bibliotheken, nur wo es klaren Mehrwert
  bringt (Filter, Suche, teilbare Links, Zufall, Ansichts-Umschalter, Zwei-Klick-Video, Drucken-Button).
  Ohne JavaScript bleiben alle Inhalte erreichbar.
- Styling: plain CSS mit CSS-Variablen; kein Tailwind nötig.
- Druckvorlagen als eigene HTML-Seiten mit Druck-CSS (A4, `@page`) → "Drucken / als PDF speichern" im Browser.
  Kein PDF-Build-Schritt. (Optional später: PDFs per Playwright beim Build erzeugen – siehe Offene Fragen.)
- Hosting: beliebiger statischer Webserver; betrieben auf dem eigenen Server des Betreibers.
- Name und Domain der Website stehen als Platzhalter in einer Konfigurationsdatei, Name „Feedback-Tools“ (entschieden), Domain noch offen.
- Werbeplätze sind als Komponenten im Layout vorbereitet und per Konfiguration ausgeschaltet (Standard: aus).

## 5. Seiten

### 5.1 Startseite `/`
- Kurze Erklärung, was Feedback-Tools sind (2–3 Sätze).
- Suchfeld + Filterleiste + Ergebnisliste aller Methoden als Karten (siehe 5.2) – Startseite IST die Übersicht.
- Kachel-Links zu den Kategorien.

### 5.2 Methodenübersicht (Teil der Startseite)
- Karte pro Methode: Titel, Kategorie-Farbe/Label, Dauer, Form-Icons (analog/digital), Druckvorlagen-Icon,
  Status-Badge bei `annahme`/`platzhalter`.
- **Filter** (Mehrfachauswahl je Gruppe, UND zwischen Gruppen, ODER innerhalb einer Gruppe):
  - Kategorie (A–G)
  - Feedbackrichtung (`richtung`)
  - Zeitpunkt (`zeitpunkt`)
  - Form (analog / digital)
  - Druckvorlage vorhanden (ja/nein)
  - optional: max. Dauer (Schieberegler, Minuten) – nutzt `dauer_min`/`dauer_max`; Methoden mit Zeitpunkt
    `dauerhaft` (0/0) erscheinen immer, da sie keine Unterrichtszeit kosten
- Volltextsuche über Titel, Aliase und Anleitung.
- Trefferanzahl anzeigen, "Filter zurücksetzen".
- Filterzustand in der URL (Query-Parameter), damit Links teilbar sind.
- "Zufällige Methode"-Button (passend zu den aktiven Filtern).

### 5.3 Methodenseite `/methoden/<id>/`
- Kopf: Titel, Kategorie, Kurzinfos (Form, Dauer, Material, Richtung, Zeitpunkt).
- Statushinweis bei `status: annahme` ("Ablauf wird noch geprüft") bzw. `platzhalter`. Bei `annahme` zusätzlich die Bitte um einen Hinweis mit Hinweis-Link (siehe 5.8).
- Anleitung (Markdown-Body: Ablauf, Tipps, Varianten).
- Download-Bereich: Link(s) zur Druckvorlage, falls `druckvorlagen` nicht leer.
- Video-Bereich, nur wenn `videos` gefüllt: Zwei-Klick-Einbettung (eigenes Vorschaubild mit Hinweis
  „Beim Abspielen werden Daten an YouTube übertragen“; das Video lädt erst nach Klick) plus direkter Link.
- Bei digitalen Methoden: Links zu passenden Tools aus `tools.yaml`.
- „Passt auch dazu“: zuerst Methoden aus dem Feld `verwandt`, aufgefüllt mit Methoden der gleichen Kategorie, max. 3.
- Druckansicht der Anleitung selbst (Druck-CSS, ohne Navigation).

### 5.4 Kategorieseite `/kategorien/<id>/`
- Beschreibung der Kategorie + alle Methoden darin.

### 5.5 Digitale Tools `/tools/`
- Tabelle/Karten aus `tools.yaml` mit Link, Zweck, Ablauf, Gerätebedarf, Datenschutzhinweis.
- Allgemeiner Hinweis: „Bitte prüfen Sie, ob das Tool an Ihrer Schule freigegeben ist.“

### 5.6 Druckvorlagen `/vorlagen/` und `/vorlagen/<id>/`
- Übersicht aller Vorlagen (Vorschaubild/Titel, zugehörige Methoden).
- Einzelseite = druckfertiges A4-Layout nach `docs/DRUCKVORLAGEN.md` + Button "Drucken".

### 5.7 Über / Impressum `/ueber/`
- Herkunft der Sammlung, Kontakt, Hinweis zu Annahmen, Lizenzhinweis (Inhalte CC BY-NC-SA 4.0).
- Impressum (Pflicht für öffentlich angebotene Websites) und Datenschutzerklärung – zunächst Platzhalter.
- Kontakt: Hinweis-Link (siehe 5.8) ohne Bezug auf eine bestimmte Methode.

### 5.8 Hinweise (seitenübergreifend)
Lehrkräfte können dem Betreiber einen **Hinweis** geben (Fehler/Korrektur, Ergänzung/Variante, Rückfrage, neue Methode).
Kein eigenes Formular und kein Backend: Die Website verlinkt nur.
- **Wo:** am Ende jeder Methodenseite, jeder Druckvorlagen-Seite und unter „Kontakt“ auf `/ueber/`. Auf Methoden- und
  Vorlagenseiten ist der Bezug vorausgefüllt (Titel und ID). In der Druckansicht ausgeblendet.
- **Zwei Wege nebeneinander:**
  - „Auf GitHub melden“: Link auf `…/issues/new?template=hinweis.yml` mit vorausgefülltem Titel und Bezug.
  - „Per E-Mail schreiben“: `mailto:` an `kontakt_email` aus `config.yaml` mit vorausgefülltem Betreff
    (z. B. „Hinweis zur Methode Daumenprobe“). Die Adresse wird als HTML-Zeichenreferenzen kodiert (kein JavaScript).
- **Issue-Vorlage** `.github/ISSUE_TEMPLATE/hinweis.yml` (GitHub-Issue-Formular), Label `needs-triage`, Felder:
  Art des Hinweises (Auswahl der vier Arten), Bezug (Text, vorausgefüllt), Beschreibung (Pflicht). Darüber fester Satz:
  keine Namen oder Daten von SuS angeben, der Hinweis ist öffentlich sichtbar.
- **Datenschutz:** Vor dem Klick wird nichts von GitHub geladen (ADR 0001 bleibt gewahrt). Die Datenschutzerklärung
  erhält einen Satz: Wer „Auf GitHub melden“ wählt, verlässt die Website; es gelten die Bedingungen von GitHub.
- **Texte** (Linktexte, Vorlagentexte, Satz in der Datenschutzerklärung) aus `content/` bzw. `config.yaml`, zunächst
  als Entwurf markiert und vom Betreiber freizugeben.

## 6. Datenmodell

Frontmatter jeder Datei in `content/methoden/` (Schema mit Pydantic abbilden, Build bricht bei Fehlern ab):

| Feld | Typ | Pflicht | Beschreibung |
| --- | --- | --- | --- |
| `id` | string (slug) | ja | = Dateiname ohne `.md` |
| `titel` | string | ja | Anzeigename |
| `aliase` | string[] | nein | weitere Namen (für Suche) |
| `kategorie` | enum A–G | ja | siehe `kategorien.yaml` |
| `richtung` | enum[] | ja | `sus-an-lehrkraft`, `peer`, `selbst`, `lehrkraft-an-klasse` |
| `zeitpunkt` | enum[] | ja | `einstieg`, `zwischendurch`, `stundenende`, `einheitsende`, `nach-praesentation`, `dauerhaft` |
| `form` | enum[] | ja | `analog`, `digital` |
| `dauer` | string | ja | Anzeigetext, z. B. "3–5 Min" |
| `dauer_min` / `dauer_max` | number | ja | Minuten für Filter; `dauerhaft` → 0 / 0 |
| `kurz` | string | nein | ein Satz Nutzen für Kopf und Karte; fehlt er, wird der erste Ablaufschritt gekürzt |
| `material` | string | ja | Anzeigetext |
| `druckvorlagen` | string[] | ja (ggf. leer) | IDs aus `DRUCKVORLAGEN.md` |
| `druckvorlage_optional` | boolean | nein | Vorlage hilfreich, aber nicht nötig |
| `tools` | string[] | nein | IDs aus `tools.yaml` |
| `status` | enum | ja | `fertig`, `annahme`, `platzhalter` |
| `hinweis` | string | nein | Text für den Statushinweis |
| `verwandt` | string[] | nein | IDs verwandter Methoden |
| `videos` | {titel, url}[] | nein | erklärende Videos (z. B. YouTube); Anzeige nur wenn gefüllt |

Body: Markdown mit den Abschnitten `## Ablauf`, optional `## Tipps`, `## Varianten`.

## 7. Design

Siehe `docs/DESIGN.md` (verbindlich). Kurz: zwei umschaltbare Ansichten mit gleichem Inhalt –
**Pinnwand** (Standard) und **Klare Ansicht**. Umschalter oben im Header, Wahl wird im Browser gespeichert.
Kategorien als ovale Papierkärtchen (Pinnwand) bzw. Liste in der Filterspalte (Klar). Mobil zuerst,
Touch-Ziele mind. 44 px, Druck immer in der klaren Ansicht.

## 8. Nicht-Ziele (Version 1)

- Keine Benutzerkonten, keine Kommentare, keine Bewertungen.
- Kein CMS-Backend. Pflege erfolgt über die Markdown-Dateien.
- Keine Einbindung von IServ.
- Keine selbst gebauten digitalen Abfrage-Tools (nur Links zu Oncoo, Mentimeter usw.).
- Keine Werbung und kein Einwilligungs-Tool (nur vorbereitete, ausgeschaltete Werbeplätze).
- Keine PDF-Erzeugung im Build; „Drucken / als PDF speichern“ im Browser reicht.
- Kein Weg für Kolleg:innen, selbst Methoden zu ergänzen (Version 2).

## 9. Akzeptanzkriterien (gesamt)

Lizenz: Inhalte CC BY-NC-SA 4.0, Code MIT (siehe `docs/adr/0002-lizenz-inhalte-cc-by-nc-sa-code-mit.md`).


1. Alle 31 Methoden und 5 Tools werden aus `content/` gerendert; `python build.py` ohne Fehler/Warnungen.
2. Filterkombination z. B. "Stundenende + analog + Druckvorlage" liefert korrekte Treffer, URL ist teilbar.
3. Jede referenzierte Druckvorlage existiert und druckt auf genau die angegebene Seitenzahl A4.
   Ausgenommen sind Druckvorlagen im Status `platzhalter`: Sie erscheinen als Seite „Vorlage folgt“ und zählen
   im Filter nicht als „Mit Druckvorlage“.
4. Lighthouse (mobil): Accessibility ≥ 95, Performance ≥ 90.
5. Keine Requests an Drittserver (Netzwerk-Tab leer außer eigener Domain), solange die Werbung ausgeschaltet ist
   und keine Lehrkraft aktiv ein Video startet.
6. Eine neue Methode lässt sich durch Anlegen einer einzigen `.md`-Datei hinzufügen.
