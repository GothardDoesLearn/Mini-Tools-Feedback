# Design

Entschieden am 2026-11-24. Referenz-Entwürfe: `docs/design/startseite-referenz.dc.html` und `docs/design/methodenseite-referenz.dc.html` (Markup und Styles als Vorlage
lesen; die Datei nutzt eine Entwurfs-Laufzeit und ist nicht direkt lauffähig – nur Aufbau, Farben und Abstände übernehmen).

## Grundsatz: zwei Ansichten, ein Inhalt

Die Seite hat zwei Ansichten (Themes) mit identischem HTML-Inhalt und identischer Funktion:

| Ansicht | Rolle | Charakter |
| --- | --- | --- |
| **Pinnwand** | Standard | Filzgraue Pinnwand, Papierkarten mit Pins, Handschrift-Überschriften – erinnert an die Fortbildungs-Pinnwand |
| **Klare Ansicht** | Alternative | Weiß, sachlich, Filterspalte links, Karten im Raster – für schnelles Lesen und Drucken |

- Umschalter oben rechts im Header ("Pinnwand" | "Klare Ansicht"), als Gruppe aus zwei `<button aria-pressed>`.
- Umsetzung über ein Attribut am `<html>`: `data-ansicht="pinnwand" | "klar"` + CSS-Variablen/Theme-Klassen.
  Kein zweites Template pro Seite; Unterschiede nur per CSS (und wo nötig per kleinen Layout-Klassen).
- Wahl in `localStorage` (`mt-ansicht`) speichern (try/catch); ohne gespeicherte Wahl → Pinnwand.
- Wahl vor dem ersten Rendern setzen (kleines Inline-Script im `<head>`), damit nichts flackert.
- Druckansicht (`@media print`) nutzt immer die klare Ansicht.
- `prefers-reduced-motion`: Drehungen/Hover-Animationen der Pinnwand abschalten.

## Kategorie-Auswahl (beide Ansichten)

- **Pinnwand:** Reihe ovaler Papierkärtchen (132×84 px) inkl. „Alle“, je mit Pin, Kurzname (Handschrift) und
  Anzahl („6 Methoden“). Leicht schräg (−3° bis +3°). Ausgewählt: gerade, angehoben (translateY −6px, scale 1.07),
  stärkerer Schatten, 3 px dunkler Rand (`outline`). Auf schmalen Bildschirmen seitlich wischbar (`overflow-x: auto`).
- **Klar:** Liste in der Filterspalte mit Farbpunkt, Kurzname und Anzahl; ausgewählt = hellblauer Hintergrund, fett.
- Mehrfachauswahl (ODER zwischen den gewählten Kategorien, entschieden 2026-11-25, wie PRD 5.2). Der Auswahlzustand
  gilt für jede gewählte Kategorie; Umsetzung als `<button aria-pressed>`. „Alle“ ist ausgewählt, wenn keine Kategorie
  gewählt ist, und hebt die Auswahl auf. Gleiche URL-Parameter in beiden Ansichten.

## Methodenseite

Aufbau (beide Ansichten gleich, siehe `methodenseite-referenz.dc.html`, Beispiel Exit-Ticket):

1. Zurück-Link zur Übersicht (Klar: Brotkrumen „Methoden / Kategorie / Methode“).
2. Kopf: Kategorie, Titel, ein Satz Nutzen (= erster Absatz bzw. Feld `kurz`), Hinweis bei `annahme`/`platzhalter`.
3. Kurzinfos: Dauer, Wann, Form, Richtung, Material (Pinnwand: weiße Schildchen, leicht gedreht; Klar: Infoleiste als `<dl>`).
4. Zwei Spalten (mobil untereinander): links „So geht's“ (nummerierte Schritte), darunter Tipp und Variante als
   Zettel/Karten nebeneinander; rechts Druckvorlage mit Mini-Vorschau + „Vorlage drucken“ / „Anleitung drucken“,
   Hinweis auf digitale Tools, „Passt auch dazu“ (zuerst Feld `verwandt`, aufgefüllt mit gleicher Kategorie, max. 3).
- Pinnwand: Titelzettel in Papierfarbe der Kategorie mit großem Pin in Pinfarbe; „So geht's“ auf weißem Zettel,
  Schrittnummern als handgeschriebene Kreise; Tipp gelb (#FFF6C7), Variante mint (#CDEEE6), Digital hellblau (#E2EDFA).
- Neues Frontmatter-Feld `kurz` (ein Satz Nutzen) für Kopf und Karten – bis es gefüllt ist, ersten Ablaufschritt kürzen.
- Video (nur wenn `videos` gefüllt): in der linken Spalte unter Tipp/Variante. Zwei-Klick-Einbettung: eigenes
  Vorschaubild (kein Bild von YouTube laden) mit Play-Symbol und Hinweis „Beim Abspielen werden Daten an YouTube
  übertragen“; erst der Klick lädt das Video. Daneben immer „Auf YouTube ansehen“ als Link.

## Werbeplätze

- Vorbereitet als Komponente, per Konfiguration ausgeschaltet (Standard). Ausgeschaltet rendert sie nichts.
- Positionen: auf der Methodenseite unter der Anleitung; in der Übersicht nach jeder n-ten Karte (n in der Konfiguration).
- Nie auf Druckvorlagen, nie in der Druckansicht (`@media print` blendet sie aus).

## Tokens

### Gemeinsam: Kategorien (Kurznamen für die Oberfläche)

| ID | Kurzname | Papier (Pinnwand) | Pin (Pinnwand) | Farbpunkt (Klar) |
| --- | --- | --- | --- | --- |
| A | Handzeichen | #FFF6C7 | #D62F2F | #2E7D32 |
| B | Im Raum | #CDE7EE | #2B4C9B | #1565C0 |
| C | Skalieren | #E3D9F2 | #E8B21E | #6A1B9A |
| D | Lernstand | #FADBD8 | #2E8B57 | #C62828 |
| E | Reflexion | #FDE3C8 | #26282C | #EF6C00 |
| F | Peer-Feedback | #CDEEE6 | #F4F4F4 | #00838F |
| G | Klassenklima | #E8E0D8 | #E07B1A | #5D4037 |
| – | Alle | #FFFFFF | #8A8A8A | #8A939E |

→ `content/kategorien.yaml` um `kurzname`, `papier`, `pin` ergänzen (bestehendes `farbe` = Farbpunkt Klar).

### Pinnwand

- Hintergrund #8F8B8E · Text #22262B · Nebentext #3C434B · Akzent (Titel, aktive Buttons) #0E7C7B
- Schrift Überschriften/Kartentitel: **Caveat** 700 · Fließtext: **Nunito** 400/600/700
- Logo-Zettel: weiß, −1,5° gedreht, zwei blaue Pins, „Feedback Tools“ (Name aus der Konfiguration) 76 px
- Methodenkarte: Papierfarbe der Kategorie, Pin oben mittig (14 px, Pinfarbe der Kategorie), Schatten
  `0 6px 14px rgba(0,0,0,.25)`, Drehung −2° bis +2°, Hover: gerade + 3 px hoch
- Filterleiste: weißer Zettel, Buttons #F2F2F2, aktiv #0E7C7B mit weißer Schrift
- Hinweis „wird geprüft!“ als roter Stempel (#9B1C1C, Caveat, 2 px Rahmen, −4°)

### Klare Ansicht

- Hintergrund #F6F7F9 · Flächen #FFFFFF · Rahmen #E3E6EA · Text #1B1F24 · Nebentext #4A525C · Akzent #1F5FBF
- Schrift: **Inter** 400/500/600/700
- Karte: weiß, 1 px Rahmen, Radius 12 px, Hover-Schatten; Farbpunkt + Kategorie, Titel 19 px
- Hinweis „wird geprüft“: Badge #FFF1D6 / Text #7A4B00

## Sprache und Anrede

- Texte an Lehrkräfte siezen („Sie“).
- Texte auf Druckvorlagen, die sich an SuS richten, duzen („du“).

## Schriften

Caveat, Nunito und Inter lokal als WOFF2 einbinden (keine Google-Fonts-Server, DSGVO). Lizenz: SIL Open Font License.

## Barrierefreiheit

- Kontrast mind. 4,5:1 für Text (Papierfarben + #22262B erfüllen das).
- Handschrift nur für Überschriften/Titel ab 22 px, nie für Fließtext.
- Touch-Ziele mind. 44 px; sichtbarer Fokus in beiden Ansichten.
