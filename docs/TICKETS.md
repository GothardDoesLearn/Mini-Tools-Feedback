# Tickets

Reihenfolge einhalten. Ein Ticket pro Claude-Code-Sitzung. Nach jedem Ticket: `npm run build` grün, committen,
Haken setzen. Jedes Ticket ist so geschnitten, dass es in eine Sitzung passt.

Prompt-Vorlage für Claude Code:
> Lies CLAUDE.md und docs/PRD.md. Bearbeite Ticket TXX aus docs/TICKETS.md – nur dieses. Lies nur die Dateien,
> die du dafür brauchst. Zeig mir am Ende, was du geändert hast, und hake das Ticket ab.

---

## Phase 1 – Grundgerüst

- [ ] **T01 – Projekt aufsetzen**
  Astro (aktuelle Version, TypeScript strict) im Repo-Root initialisieren, ohne Beispielinhalte.
  Skripte `dev`, `build`, `check`. `src/config.ts` mit Platzhaltern für Website-Name („Mini-Tools“) und Domain sowie Werbe-Schalter (Standard: aus). `.gitignore`.
  *Fertig wenn:* `npm run build` erzeugt eine leere Startseite in `dist/`.

- [ ] **T02 – Content-Schema**
  Content Collection `methoden` aus `content/methoden/` mit Zod-Schema gemäß PRD §6 (inkl. optionaler Felder `kurz` und `videos`).
  `kategorien.yaml`, `filter.yaml`, `tools.yaml` als Daten laden (typisiert).
  Prüfen: `id` = Dateiname; alle `druckvorlagen`-, `tools`-, `verwandt`-IDs existieren (Build-Fehler sonst).
  *Fertig wenn:* `npm run check` validiert alle 31 Dateien ohne Fehler.

- [ ] **T03 – Layout & Ansicht „Klar“**
  Basis-Layout (Header mit Navigation: Methoden, Druckvorlagen, Digitale Tools, Über; Footer) nach `docs/DESIGN.md`,
  zuerst die klare Ansicht. CSS-Variablen pro Ansicht unter `[data-ansicht="klar"]`, Inter lokal, Druck-CSS-Basis.
  `kategorien.yaml` um `kurzname`, `papier`, `pin` ergänzen (Werte in DESIGN.md).
  *Fertig wenn:* Layout auf 375 px und 1280 px sauber, Tastatur-Fokus sichtbar.

- [ ] **T03b – Ansicht „Pinnwand“ + Umschalter**
  Pinnwand-Theme unter `[data-ansicht="pinnwand"]` (Caveat + Nunito lokal), Umschalter im Header, Speicherung in
  `localStorage`, Inline-Script gegen Flackern, Standard = Pinnwand, `prefers-reduced-motion`, Druck = klar.
  Referenz: `docs/design/startseite-referenz.dc.html`.
  *Fertig wenn:* Umschalten wirkt sofort auf allen Seiten, Wahl bleibt nach Neuladen erhalten.

## Phase 2 – Inhalte anzeigen

- [ ] **T04 – Methodenseite**
  `/methoden/[id]/` nach `docs/DESIGN.md` → Methodenseite und `docs/design/methodenseite-referenz.dc.html`: Kopf, Kurzinfos, Hinweisbox (annahme/platzhalter), Markdown-Body, Download-Bereich,
  Tool-Links, verwandte Methoden, Video-Bereich (Zwei-Klick-Einbettung, nur wenn `videos` gefüllt; mit einer Testmethode prüfen).
  *Fertig wenn:* alle 31 Seiten bauen; Daumenprobe, Fahrstuhlmethode (annahme) und Wimmelbild (platzhalter) geprüft.

- [ ] **T05 – Methodenkarten & Übersicht (ohne Filter)**
  Karten-Komponente in beiden Ansichten (Papierkarte mit Pin bzw. weiße Karte), Kategorie-Ovale (Pinnwand) bzw. Kategorie-Liste (Klar) noch ohne Funktion, Startseite mit Intro und allen Methoden, sortiert nach Kategorie, dann Titel.
  *Fertig wenn:* 31 Karten sichtbar, Karte verlinkt auf Methodenseite.

- [ ] **T06 – Kategorie- und Toolseiten**
  `/kategorien/[id]/` und `/tools/`.
  *Fertig wenn:* 7 Kategorieseiten + Toolseite bauen, Links funktionieren.

## Phase 3 – Filter & Suche

- [ ] **T07 – Filterleiste**
  Filtergruppen aus `filter.yaml` (Kategorie, Richtung, Zeitpunkt, Form, Druckvorlage). Kategorie-Ovale/-Liste als Einfachauswahl mit Auswahlzustand laut DESIGN.md. Daten als
  `data-*`-Attribute an den Karten, Filterung per Vanilla-JS. Trefferzahl, Zurücksetzen. Ohne JS: alle Karten sichtbar.
  *Fertig wenn:* Kombination "Stundenende + analog + Druckvorlage ja" zeigt genau die erwarteten Methoden.

- [ ] **T08 – Filter in der URL + Zufallsbutton**
  Zustand ↔ Query-Parameter synchronisieren; "Zufällige Methode" aus aktueller Treffermenge.
  *Fertig wenn:* Link mit Filtern in neuem Tab öffnet identische Ansicht.

- [ ] **T09 – Volltextsuche & Dauer-Filter**
  Suche über Titel, Aliase, Anleitungstext (vorab generierter JSON-Index, keine externe Bibliothek nötig).
  Dauer-Schieberegler (max. Minuten).
  *Fertig wenn:* Suche "Hand" findet 5-Finger-Methode; Dauer ≤ 2 Min filtert korrekt.

## Phase 4 – Druckvorlagen

- [ ] **T10 – Vorlagen-Infrastruktur**
  `/vorlagen/` (Übersicht) und `/vorlagen/[id]/` mit A4-Druck-CSS (`@page { size: A4; margin: 12mm }`),
  Button "Drucken". Daten der Vorlagen aus `docs/DRUCKVORLAGEN.md` nach `content/druckvorlagen.yaml` übertragen.
  *Fertig wenn:* eine Beispielvorlage (Exit-Ticket) druckt korrekt auf 1 Seite A4.

- [ ] **T11 – Vorlagen Gruppe 1 (Karten zum Hochhalten)**
  ampelkarten, smiley-karten, wettersymbole, eckenschilder, feedback-hand.

- [ ] **T12 – Vorlagen Gruppe 2 (Skalen & Plakate)**
  zielscheibe, skalen-plakat, lernrad, checkliste.

- [ ] **T13 – Vorlagen Gruppe 3 (Reflexion & Peer-Feedback)**
  exit-ticket (final), reflexionskarten, wuerfelnetz, fragebogen, sterne-wunsch-karte, www-karte, burger,
  beobachtungsbogen.

- [ ] **T14 – Platzhalter-Vorlage Wimmelbild**
  Seite mit Hinweis "Vorlage folgt" (kein fremdes Bild verwenden). Zählt im Filter nicht als „Mit Druckvorlage“.

## Inhalte (unabhängig von der Technik)

- [ ] **C01 – Feld `kurz` für alle 31 Methoden**
  Claude entwirft je einen Satz Nutzen, der Betreiber gibt gesammelt frei.

- [ ] **C02 – Herkunft der Texte prüfen**
  Alle 31 Anleitungen auf Herkunft prüfen; wo unsicher, neu formulieren (Entwurf Claude, Freigabe Betreiber).
  Blockiert nur das Einschalten von Werbung, nicht die Entwicklung.

## Phase 5 – Feinschliff & Veröffentlichung

- [ ] **T15 – Über-Seite, 404, Metadaten**
  `/ueber/` (mit Lizenzhinweis), Impressum- und Datenschutz-Seite (Platzhalter), eigene 404, `<title>`/Description je Seite, Favicon-Platzhalter.

- [ ] **T15b – Werbeplätze vorbereiten**
  Werbeplatz-Komponente nach `docs/DESIGN.md` → Werbeplätze, per Konfiguration ausgeschaltet; nie auf Druckvorlagen/Druckansicht.
  *Fertig wenn:* ausgeschaltet kein zusätzliches HTML; testweise eingeschaltet erscheinen leere Platzhalter an den richtigen Stellen, nicht im Druck.

- [ ] **T16 – Qualitätsprüfung**
  Lighthouse mobil, Tastaturtest, Prüfen auf Drittanfragen, Link-Check. Befunde beheben.
  *Fertig wenn:* Akzeptanzkriterien PRD §9 erfüllt.

- [ ] **T17 – Deployment**
  Anleitung `docs/DEPLOYMENT.md` (Build hochladen per rsync/SFTP auf eigenen Server) + optional Skript `deploy.sh`.
