# Architektur und Erweiterungspunkte

Wie der Code aufgebaut ist, wo man etwas ergänzt und welche Fallen es gibt. Was die Dateien selbst klar sagen,
steht hier nicht; im Zweifel gilt der Code. Technik-Entscheidung: `docs/adr/0003-…`.

## Ablauf eines Builds

```text
build.py (nur Kommandozeile)
  generator/build.py: build()
    config.yaml        -> SiteConfig        (generator/config.py; einzige Stelle für Name, Domain, Werbe-Schalter)
    content/           -> SiteData          (generator/content.py: load_site, Pydantic-Schema, Querverweise)
    generator/seiten/* -> HTML in dist/     (jede Datei meldet ihre Seiten mit @seite an)
    static/css/<name>/ -> dist/static/css/<name>.css   (generator/css.py fügt die Dateien zusammen)
    static/ (Rest)     -> dist/static/
```

- Inhaltsfehler werfen `ContentError("<datei>: <ursache>")`. Die Kommandozeile zeigt sie ohne Traceback und
  endet mit Code 1; `--check` prüft nur Schema und Querverweise.
- Erlaubte Werte (Kategorien, Filterwerte) kommen aus `kategorien.yaml`/`filter.yaml`, nie aus dem Code. Nur der
  Bearbeitungsstand ist fest: Typ `Status` und Konstante `PLATZHALTER` in `generator/content.py`.
- Hilfen auf `SiteData`: `kategorie(id)`, `methoden_mit_vorlage(id)`, `tools_hinweis`. Die Zuordnung Methode →
  Druckvorlage steht nur im Feld `druckvorlagen` der Methode.

## Neue Seite

Neue Datei `generator/seiten/<name>.py`; Anleitung im Docstring von `generator/seiten/__init__.py`. Eine
gemeinsame Liste gibt es nicht. Die Reihenfolge ist alphabetisch nach Datei und Funktion.

- `write_page(env, output_dir, "<pfad>", "<template>.html", **kontext)` aus `generator/render.py` schreibt
  `<pfad>/index.html`.
- **Jede Seite braucht einen eigenen Titel und eine eigene Beschreibung** (`seitentitel=`, `beschreibung=`),
  sonst schlägt `tests/test_seitenkopf.py` fehl. Für Beschreibungen aus Inhalten: Filter `| kurzbeschreibung`.
- Aktiver Menüpunkt: `aktiver_bereich="methoden"|"vorlagen"|"tools"|"ueber"`.
- Markdown aus `content/` immer mit `| markdown` rendern; das kennzeichnet externe Links (Pfeil,
  Screenreader-Hinweis, `rel`).
- Links auf Kategorieseiten immer über `Kategorie.url`. Die URL-Form ist noch offen (#50).

## Templates

- Jinja2 mit `StrictUndefined`: Ein fehlender Kontextwert bricht den Build ab.
- Wiederverwendbare Teile: `_karte.html` (Methodenkarte), `_statushinweis.html`, `_werbeplatz.html`,
  `_video.html`, `_filterleiste.html`.
- Texte zum Bearbeitungsstand (annahme, platzhalter, entwurf) nur aus `generator/status.py`, im Template als
  `status_texte[art][status]`.
- „Hat die Methode eine Druckvorlage?“ nur über `hat_druckvorlage` (`generator/karten.py`): Vorlagen mit Status
  `platzhalter` zählen nicht (PRD §9.3).
- Werbeplätze nur über `werbeplatz("<position>")`. Ohne `werbung_aktiv` rendert das Makro nichts. Nie auf
  Vorlagenseiten.

## CSS und die zwei Ansichten

- `static/css/site/` und `static/css/druckvorlage/` werden in Dateinamen-Reihenfolge zusammengefügt. Die Nummern
  sind die Kaskade: `00–06` Grundlagen, `10–41` Komponenten, `50` Fokus, `60–69` Pinnwand, `90` Druck. Eine neue
  Komponente bekommt eine eigene Datei statt Zeilen am Ende einer gemeinsamen.
- Tokens: ansichtsunabhängig auf `:root`, Farben und Schriften unter `:root, [data-ansicht="klar"]`. Die Ansicht
  Pinnwand setzt dieselben Token-Namen, **nur innerhalb `@media screen`**, damit der Druck automatisch die Ansicht
  Klar nutzt. Ein Test prüft, dass „pinnwand“ sonst nirgends im CSS vorkommt; darum heißen Hilfsklassen
  z. B. `.nur-filz`.
- Kontrast: Auf dem Filz der Pinnwand (#8F8B8E) nur `--farbe-text` (4,53:1) oder Weiß ab großem Text. Darum ist
  `--farbe-link` dort die Textfarbe. Die Titelschrift (Caveat) nur ab 22 px; ein Test prüft jede Regel.
- Ansichtsabhängiges über das Attribut `data-ansicht` am `<html>` stylen, nicht per JavaScript; sonst flackert es.
- Schriften: `templates/ansicht.js` lädt die Schriftdateien der gewählten Ansicht per `preload` vor, sonst
  verschiebt der späte Schriftwechsel das Layout (Lighthouse CLS). Neue oder geänderte Schriftdatei in
  `00-schriften.css` darum auch dort eintragen; `tests/test_ansicht_umschalter.py` prüft, dass beides übereinstimmt.
- Bedienelemente, die nur mit JavaScript funktionieren: `html:not([data-js]) .x { display: none }`.
- Klassen deutsch und BEM-artig (`.kopf__rechts`, `.karte__kategorie--link`). Karten auf Druckvorlagen heißen
  `.druckkarte`, weil `.karte` die Methodenkarte ist.

## JavaScript: Filter der Startseite

Alles in `static/js/filter.js`. Der Kopfkommentar listet die Erweiterungspunkte:

1. Zustand in `zustandLesen()` ergänzen.
2. Prüfung `function (karte, zustand)` an `PRUEFUNGEN` anhängen.
3. Bei Bedienung `bedient()` aufrufen (filtert und legt einen Verlaufseintrag an). Beim Tippen stattdessen
   `aktualisieren(); urlSchreiben("ersetzen")`, sonst entsteht pro Tastendruck ein Eintrag.
4. Für teilbare Links eine Zeile `urlParameter(name, lesen, anwenden)` vor `// Start`.

- Karten werden über `data-methode` gefunden. Werbeplätze im Raster haben das Attribut nicht und bleiben beim
  Filtern unberührt.
- Kategorien nur über `kategorienAnzeigen(ids)` setzen, weil es „Alle“ mitpflegt.
- Weitere Skripte: `templates/ansicht.js` (inline im `<head>`, Speicherschlüssel `mt-ansicht`),
  `static/js/video.js` (nur auf Methodenseiten mit Video), `static/js/drucken.js`.

## Druckvorlage hinzufügen

1. `templates/vorlagen/<id>.html` anlegen; die Datei ersetzt „Vorlage folgt“ automatisch. Vorbild:
   `exit-ticket.html`.
2. Bausteine aus `vorlagen/_blatt.html`: `{% call blatt("<Titel> – Seite N", quer=false) %}` ist genau eine
   A4-Seite samt Fußtext. Dazu `feld(...)` und gemeinsame `symbole`. Kreisscheiben: `vorlagen/_scheibe.html`.
   Große, vorlagenspezifische SVGs als Makro in der eigenen Vorlage.
3. Styles in eine eigene Datei `static/css/druckvorlage/50-<id>.css`. Maße in mm, druckbar 186×272 mm (hoch)
   bzw. 273×185 mm (quer). Linien als `border`; Farbe nur als Zusatz per SVG-`fill`, weil Hintergründe nicht
   gedruckt werden.
4. Texte wörtlich aus `docs/DRUCKVORLAGEN.md`. Was schon in einer Methode steht, ableiten statt kopieren
   (Beispiel `satzanfaenge()` in `generator/vorlagen.py`).
5. Seitenzahl prüfen: `python tools/druck_pruefen.py <id>`. Ein Test zählt zusätzlich die
   `<section class="blatt`-Elemente.

- SVG-`<text>`: tspans ohne Leerraum dazwischen schreiben, sonst rücken Folgezeilen ein.

## Tests

- Immer in `tmp_path` bauen. Inhalte für Tests über die Helfer in `tests/test_methoden.py` und
  `tests/test_stammdaten.py` anlegen, nie `content/` ändern.
- JavaScript wird mit Node und einem Mini-DOM getestet (Muster: `tests/test_filterleiste.py`). Lokal ohne Node
  übersprungen, in der CI Pflicht (`tests/conftest.py`).
- Drittserver-Test (`tests/test_cli.py`): Er prüft alles, was der Browser selbst lädt. Externe URLs darum nie in
  Attributen, die auf `src` enden, auch nicht `data-…-src`.
- Neue Tests für eine eigene Komponente in eine eigene Datei; das vermeidet Merge-Konflikte bei paralleler Arbeit.
- Optik prüfen: `python tools/druck_pruefen.py --screenshot / --breite 375 --ansicht klar --out <ordner>` (in Git Bash mit
  `MSYS_NO_PATHCONV=1` davor).
