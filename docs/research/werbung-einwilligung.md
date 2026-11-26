# Recherche: Einwilligungs-Tool und Werbenetzwerk

Grundlage für die Entscheidung des Betreibers in #45 (Issue #77). Das hier ist **keine Entscheidung**: Es wurden keine
Konten angelegt, keine Bedingungen akzeptiert und kein Code geändert. Alle Quellen wurden am **2026-11-26** abgerufen,
sofern nicht anders vermerkt. Rechtliche Punkte sind **prüfbedürftig, keine Rechtsberatung**.

## Zusammenfassung

- **AdSense verlangt für personalisierte Werbung im EWR, im Vereinigten Königreich und in der Schweiz ein von Google
  zertifiziertes Einwilligungs-Tool (CMP) mit IAB TCF**, seit dem 16.01.2024 (Schweiz: 31.07.2024). Ohne ein solches
  Tool gibt es höchstens nicht personalisierte oder „eingeschränkte“ Anzeigen (Limited Ads). [G1]
- **Kein geprüftes quelloffenes, selbst hostbares Tool ist von Google zertifiziert oder unterstützt TCF.** Klaro! und
  Orestbida CookieConsent stehen weder auf Googles Liste noch auf der IAB-CMP-Liste. CookieConsent schreibt selbst, es
  sei „kein CMP“, setze TCF nicht um und funktioniere seit Januar 2024 nicht mehr mit AdSense. [G1, I1, C1]
- **Selbst hostbar *und* zertifiziert ist nur CCM19** (Download-Version, Lizenzgebühr). Es braucht aber PHP 8.2 auf dem
  Server, und TCF ist ein Zusatzmodul. Das widerspricht „statische Seite ohne Server-Backend“ (ADR 0003). [G1, X1, X2]
- **Zertifizierte SaaS-Tools** (z. B. Googles eigenes „Privacy & messaging“, Cookiebot, Usercentrics) laden ihr Skript
  von Fremdservern. Im eingeschalteten Zustand gibt es also schon vor der Einwilligung eine Drittanfrage. Das verstößt
  gegen den Geist von ADR 0001, nicht aber gegen den Wortlaut (die strengen Regeln gelten nur bei ausgeschalteter
  Werbung). [G1, G5; Lieferweg teils nicht belegt, siehe Offene Punkte]
- **Netzwerke:** Realistisch zugänglich ist für eine kleine Website derzeit nur **Google AdSense**. Es gibt keine
  Mindestreichweite, die Auszahlung beginnt ab 70 €. [A1, A6] Die geprüften datenschutzfreundlichen bzw.
  Premium-Alternativen setzen hohe Reichweiten voraus: EthicalAds 50.000 Seitenaufrufe pro Monat und
  Entwickler-Publikum, Ezoic 250.000 Nutzer pro Monat. Beides ließ sich nur über Suchtreffer belegen. Deutsche
  Vermarkter nennen keine öffentlichen Aufnahmebedingungen. [E1, Z1, N1]
- **ADR-konform in beiden Zuständen** ist nur eine Lösung ohne fremde Anzeigenserver: ein selbst gehostetes Tool
  (Klaro! oder CookieConsent) nur für YouTube, dazu höchstens selbst ausgelieferte Anzeigen von der eigenen Domain
  (Direktvermarktung/Sponsoring).
- **Folgen bei AdSense:** eine erweiterte Datenschutzerklärung (#44, mit Google-Pflichtangaben), ein Banner mit
  gleichwertiger Ablehnen-Möglichkeit, ein Link zum Widerruf auf jeder Seite, `ads.txt` und eine Kennzeichnung der
  Werbeplätze als „Anzeige“. Die Werbeplatz-Komponente bekäme dann keine `aria-hidden`-Hülle mehr. Lighthouse-Ziel und
  PRD §9 Nr. 5 sind für den eingeschalteten Zustand neu festzulegen. [D1, A3, A5]

## 1. Einwilligungs-Tools

### Vergleich

| Tool | Selbst hostbar, ohne Drittanfrage vor Einwilligung | Ohne Backend | Lizenz / Kosten | Deutsch | Barrierefreiheit | IAB TCF / Google-zertifiziert | YouTube mitverwalten |
|---|---|---|---|---|---|---|---|
| **Klaro!** (kiprotect/klaro) | ja: `dist`-Dateien bzw. npm; CDN optional [K1] | ja, reines JS [K1] | BSD-3, kostenlos [K1] | ja, `de.yml` mitgeliefert [K2] | offene Issues zu fehlenden zugänglichen Namen von Dialogen, seit 2019 offen: „Support of W3C's accessibility standards“ (#100, #503, #558) [K3] | nein: nicht auf Google- oder IAB-Liste [G1, I1]; TCF in der README nicht erwähnt [K1] | ja: `contextualConsentOnly`, Beispiel-Dienst `youtube` in der Beispiel-Konfiguration [K4] |
| **CookieConsent v3** (orestbida) | ja: `dist` bzw. npm [C2] | ja, Vanilla-JS [C1] | MIT, kostenlos; v3.3.0 vom 03.11.2026 [C2] | keine mitgelieferten Übersetzungen, Texte selbst schreiben [C1, C3] | Fokusfalle (`src/utils/focus-trap.js`) und ARIA-Attribute im Quelltext; keine dokumentierte Barrierefreiheitsaussage gefunden [C4] | nein: „does not implement the IAB Framework – TCF“, „is not a CMP“; Hinweis: AdSense, Ad Manager und AdMob „will no longer work with CookieConsent starting from January 2024“ [C1] | ja, mit Zusatz **iframemanager** (MIT, v1.3.0 vom 08.09.2024); dessen Beispiel lädt Vorschaubilder von `i3.ytimg.com`, eigene Bilder per `data-thumbnail` sind möglich [C5] |
| **Eigene Lösung** (vorhandene Zwei-Klick-Einbettung erweitern) | ja | ja | eigener Code | ja | eigene Verantwortung | nein | ja, Grundlage besteht (`templates/_video.html`) |
| **CCM19** (Papoo Software & Media GmbH) | ja, Download-/On-Premise-Version [X1] | **nein:** braucht PHP ≥ 8.2 und mod_rewrite bzw. NGINX-Konfiguration [X2] | kommerziell; Starter 7,90 €/Monat inkl. USt., 2 Domains, 20.000 Impressionen, auch als Download; TCF nur „als Zusatzmodul“ ab Business (19,90 €/Monat) [X1] | ja, deutscher Hersteller | nicht geprüft | **ja:** „CCM19 CMP“, TCF-ID 343, auf Googles Liste [G1, I1]; ob das auch für die Download-Version gilt, ist **unklar** | nicht geprüft |
| **Google „Privacy & messaging“** | nein, von Google bereitgestellt (Lieferweg nicht im Detail belegt) | ja (Nachricht wird in AdSense erstellt) | kostenlos für AdSense-Konten (Kosten auf der Hilfeseite nicht genannt) [G4] | nicht belegt | nicht geprüft | ja: „Google LLC CMP“, TCF-ID 300 [G1, I1] | nicht belegt; Anbieter außerhalb von Google muss man selbst auflisten [G4] |
| **Cookiebot** (Usercentrics) | nein, SaaS (Hosting-Ort des Skripts auf der Preisseite nicht genannt) | ja | Free: 1 Domain, **50 Unterseiten** (Build aktuell 63 HTML-Seiten); TCF nur in Premium-Plänen ab 7 €/Monat (Premium Lite) [B1] | nicht geprüft | nicht geprüft | ja: „Cookiebot CMP“, TCF-ID 134 [G1] | nicht geprüft |

Weitere zertifizierte SaaS-Tools auf Googles Liste (u. a. Usercentrics, consentmanager, Didomi, Sourcepoint, Osano)
sowie die WordPress-Plugins Borlabs Cookie und Real Cookie Banner (passen nicht zu einer statischen Seite) wurden nicht
einzeln bewertet. Googles Liste hat rund 148 Einträge. [G1]

### Warum ein quelloffenes Tool kaum zertifiziert sein kann

- Ein CMP muss sich bei IAB Europe registrieren und eine jährliche CMP-Mitgliedschaft beantragen, um am TCF
  teilzunehmen. Die Höhe der Gebühr nennt die Seite nicht. [I2]
- Google nennt drei Wege: eigenes Tool bauen und zertifizieren lassen, Googles „Privacy & messaging“ nutzen oder ein
  zertifiziertes Drittanbieter-CMP einsetzen. [G4]
- Die IAB-Liste (Stand 19.11.2026) führt 207 aktive CMPs. Alle hier genannten Anbieter sind als kommerziell
  gekennzeichnet; Klaro!/KIProtect und CookieConsent fehlen. [I1]
- Bei CookieConsent gibt es einen Feature-Wunsch „Become a Google Certified CMP“ (#562, 25.08.2023). Die Dokumentation
  verneint TCF weiterhin. [C1, C6]

## 2. Werbenetzwerke

### Vergleich

| | **Google AdSense** | **EthicalAds** | **Ezoic** | **Deutsche Vermarkter** (z. B. netpoint media) |
|---|---|---|---|---|
| Aufnahme | ab 18 Jahren, Zugriff auf HTML-Quelltext, „high-quality, original“ Inhalte, Einhaltung der Programmrichtlinien; keine Mindestreichweite genannt [A1] | laut Suchtreffer **≥ 50.000 Seitenaufrufe/Monat**, „developer-focused sites“ [E1, unbestätigt] | laut Suchtreffer **≥ 250.000 monatlich aktive Nutzer** (seit Feb. 2026), darunter „Incubator“-Programm [Z1, unbestätigt] | keine öffentlichen Bedingungen gefunden, Anfrage beim Vermarkter nötig [N1] |
| Impressum / Datenschutzerklärung | Datenschutzerklärung mit Angaben zu Google-Cookies, Drittanbietern und Opt-out-Möglichkeiten [A5]; Impressumspflicht ergibt sich aus § 5 DDG, nicht aus AdSense [R3] | nicht geprüft | laut Suchtreffer Datenschutzerklärung mit Ezoic-Angaben, `ads.txt` [Z1, unbestätigt] | – |
| Einwilligungs-Tool | personalisiert nur mit Google-zertifiziertem TCF-CMP; sonst nicht personalisierte oder Limited Ads [G1, G2] | laut Hersteller keine Cookies/kein Tracking (nicht selbst geprüft, Seite nicht erreichbar) | laut Suchtreffer das Ezoic-eigene CMP [Z1, unbestätigt] | – |
| Dichte / Platzierung | keine feste Obergrenze; nicht mehr Anzeigen als Publisher-Inhalt, wobei Weißraum, Kopf- und Fußbereich sowie Links **nicht** als Inhalt zählen [A2]; keine Platzierung, die zu versehentlichen Klicks führt (Navigation in der Nähe), Kennzeichnung als „Advertisements“/„Sponsored Links“ [A3]; keine Anzeigen auf Seiten ohne Inhalt [A4] | laut Suchtreffer Mindest-CTR 0,1 % [E1, unbestätigt] | nicht geprüft | – |
| Kontextbezogen / nicht personalisiert | ja: nicht personalisierte Anzeigen nutzen Kontext und grobe Lage, verwenden Cookies aber weiter für Frequency Capping und Berichte; Einwilligung „where legally required“ [A7]. Limited Ads: keine Personalisierung, aber Cookies/Local Storage nur zur Erkennung ungültiger Zugriffe, auch **ohne Einwilligung**, in AdSense abschaltbar [G2] | Kernkonzept des Netzwerks (kontextbezogen) | nicht geprüft | – |
| Auszahlungsschwelle | 70 € (Konten in EUR) [A6] | laut Suchtreffer 50 US-$ [E1, unbestätigt] | nicht geprüft | – |
| Inhalte rund um Schule | Websites, die unter COPPA fallen (US-Kinder unter 13), sind Google zu melden bzw. zu taggen; keine interessenbasierte Werbung an Nutzer, die bekanntermaßen unter 13 sind [A8]. Taggen schaltet interessenbasierte Werbung und Remarketing ab; Google kann eine Website auch selbst als kindgerichtet behandeln [A9]. Zielgruppe hier sind Lehrkräfte, nicht SuS → Einordnung **prüfbedürftig** | – | – | – |
| Eignung für dieses Projekt | **zugänglich** | wohl nicht (Reichweite, Themenfokus) | nicht (Reichweite) | offen |

Nicht weiter verfolgt: Media.net (keine Aussage zu Sprache/Land gefunden; Aufnahme nach Ermessen, `ads.txt` Pflicht
[M1]); Netzwerke für Krypto- oder Pop-under-Werbung (passen nicht zur Zielgruppe).

### Werbeplatz nach jeder 6. Karte (AdSense)

- 31 Methodenkarten bei `werbung_nach_karten: 6` ergeben 5 Werbeplätze in der Übersicht (der letzte entfällt wegen
  `not loop.last`). Das bleibt unter der Regel „nicht mehr Anzeigen als Inhalt“ [A2]. Ob Kartenteaser als
  „Publisher-Inhalt“ zählen oder als „Links zu anderen Inhalten“, die Google ausdrücklich nicht mitrechnet, ist
  **unklar**.
- Prüfbedürftig: Wenn der Filter (JavaScript) Karten ausblendet, können Werbeplätze direkt aufeinander folgen oder
  neben wenigen Treffern stehen.
- Feste Höhe per CSS (die Komponente reserviert bereits `min-height: 90px`) ist laut Google der einzige sichere Weg,
  Layoutverschiebungen zu vermeiden. [P1]

## 3. Kombinationen und ADR 0001

ADR 0001: Ohne Einwilligung keine Drittanfragen. Die strengen Regeln gelten verbindlich nur, solange die Werbung aus
ist; vor dem Einschalten braucht es ein Einwilligungs-Tool, an das auch YouTube angebunden wird.

| # | Kombination | Funktioniert technisch? | ADR 0001, Werbung **aus** | ADR 0001, Werbung **an** |
|---|---|---|---|---|
| K1 | Klaro! oder CookieConsent (selbst gehostet) **nur für YouTube**, keine Werbung bzw. nur selbst ausgelieferte Anzeigen (Bild und Link von der eigenen Domain) | ja | erfüllt (Tool lädt von eigener Domain) | erfüllt, solange die Anzeigen keine Fremdserver ansprechen und nichts auf dem Endgerät speichern (§ 25 TDDDG, prüfbedürftig) |
| K2 | **AdSense + Google „Privacy & messaging“** | ja, zertifiziert, personalisierte Anzeigen möglich [G1, G4] | erfüllt, wenn das AdSense-Skript bei `werbung_aktiv: false` nicht eingebunden wird | **verletzt den Geist:** Banner und AdSense-Code kommen von Google, also gibt es vor der Einwilligung eine Drittanfrage. YouTube lässt sich nicht nachweislich mit demselben Tool steuern |
| K3 | **AdSense + zertifiziertes SaaS-CMP** (z. B. Cookiebot Premium, Usercentrics) | ja [G1, B1] | erfüllt (nicht eingebunden) | wie K2: CMP-Skript von Fremdserver (Lieferweg nicht im Detail belegt). YouTube-Steuerung bei diesen Tools nicht geprüft |
| K4 | **AdSense + CCM19 Download-Version** auf eigenem Server | ja, wenn Zertifizierung und TCF-Modul auch für die Download-Version gelten (**unklar**) [G1, X1] | erfüllt | Tool selbst ohne Drittanfrage. Verstößt aber gegen ADR 0003 (PHP-Backend) und braucht einen PHP-fähigen Server |
| K5 | **AdSense nur nicht personalisiert/Limited + selbst gehostetes Tool ohne TCF** (Klaro!/CookieConsent; AdSense-Skript erst nach Einwilligung geladen) | **eingeschränkt und riskant:** ohne TC-String versucht Google Limited Ads [G2]. Googles Ersatz-Banner („Maximize message coverage“) ist standardmäßig an und springt bei fehlendem TC-String ein [G3]; abschalten müsste man es selbst. CookieConsent nennt AdSense ausdrücklich „no longer work[ing]“ [C1]. Ob das die EU-Einwilligungsrichtlinie von Google erfüllt (Nachweise, Widerruf, Nennung der Beteiligten) [A10], ist **prüfbedürftig** | erfüllt | formal erfüllt (nichts vor der Einwilligung). Geringere Erlöse, unklare Richtlinienlage |
| K6 | EthicalAds oder Ezoic | Aufnahme bei aktueller Reichweite unwahrscheinlich [E1, Z1] | – | – |

## 4. Folgen für das Projekt

### Rechtlicher Rahmen (nur mit Quelle, prüfbedürftig, keine Rechtsberatung)

- **§ 25 Abs. 1 TDDDG:** Speichern auf dem Endgerät oder Auslesen braucht eine Einwilligung auf Grundlage klarer und
  umfassender Informationen nach DSGVO. **Abs. 2:** Ausnahme, wenn es unbedingt erforderlich ist für einen
  „vom Nutzer ausdrücklich gewünschten digitalen Dienst“. [R1]
- **DSK, OH Digitale Dienste v1.2 (Nov. 2024):**
  - Wirtschaftliche Erforderlichkeit für das Geschäftsmodell begründet keine Ausnahme (Rn. 78).
  - Werbeanzeigen und Videos sind typische Drittinhalte, deren Einbindung personenbezogene Daten (mindestens die
    IP-Adresse) an den Drittserver offenlegt und eine Rechtsgrundlage nach Art. 6 DSGVO braucht (Rn. 101).
  - Erst nach aktiver Handlung darf gespeichert, ausgelesen oder verarbeitet werden (Rn. 122).
  - Eine Ablehnen-Möglichkeit auf erster Ebene ist nötig, wenn das Banner Inhalte versperrt; bei „gängigen
    Ausgestaltungen“ sei das „sehr häufig“ der Fall (Rn. 124 f.). Der Widerruf muss so einfach sein wie die
    Einwilligung (Rn. 126).
  - Den Einwilligungsstatus speichert man in der Regel in einem Cookie ohne Nutzerkennung (UID). Die Prozesse und
    früheren Banner-Texte sind als Nachweis aufzubewahren (Rn. 84 f.). [D1]
- **Impressum:** § 5 Abs. 1 DDG gilt für „geschäftsmäßige, in der Regel gegen Entgelt angebotene digitale Dienste“.
  Mit Werbeeinnahmen dürfte das eher zutreffen (prüfbedürftig). PRD §5.7 sieht das Impressum ohnehin vor. [R3]
- **Google EU-Einwilligungsrichtlinie:** Einwilligung für Cookies/Local Storage, wo gesetzlich nötig, und für
  personalisierte Werbung; Nachweise aufbewahren; klare Widerrufsanleitung; jeden Beteiligten benennen. [A10]

### Datenschutzerklärung (#44)

- Solange die Werbung aus ist: wie bisher, plus Abschnitt „Einwilligungs-Tool“, sobald es für YouTube eingebaut wird
  (welcher Eintrag im Speicher, welcher Zweck, wie man widerruft).
- Mit AdSense zusätzlich: Google und Partner setzen Cookies für Anzeigen auf Basis früherer Besuche; die beteiligten
  Drittanbieter samt Links; Opt-out über die Google-Anzeigeneinstellungen bzw. aboutads.info [A5]; Datenübermittlung in
  Drittländer (DSK Rn. 101 ff.); Rechtsgrundlagen und Widerruf. Formulierungen nur als Entwurf, der Betreiber gibt frei
  (AGENTS.md).

### Seitenaufbau

- Banner beim ersten Besuch, ohne Impressum oder Datenschutzerklärung zu versperren (DSK, Fassung 2021, laut Suchtreffer;
  in v1.2 nicht gegengeprüft). Ablehnen-Schaltfläche gleichwertig auf erster Ebene [D1].
- Dauerhafter Link „Datenschutz-Einstellungen“ (z. B. im Fußbereich) für den Widerruf [D1 Rn. 126; A10].
- Banner nicht in Druckvorlagen und nicht in der Druckansicht (analog zu `90-druck.css`).
- Bei AdSense: Datei `ads.txt` im Wurzelverzeichnis (Pflicht bei Media.net [M1], bei Ezoic laut Suchtreffer [Z1]; für
  AdSense hier nicht eigens belegt).
- Im Build: Das Einwilligungs-Tool hängt sinnvollerweise an einem eigenen Schalter oder an `werbung_aktiv`, damit bei
  ausgeschalteter Werbung PRD §9 Nr. 5 unverändert gilt.

### Werbeplatz-Komponente (`templates/_werbeplatz.html`)

- `aria-hidden="true"` passt zum leeren Platzhalter. Mit echten Anzeigen (fokussierbare Links) ist es falsch;
  Lighthouse/axe melden fokussierbare Elemente in `aria-hidden`-Containern. Stattdessen eine Kennzeichnung „Anzeige“
  (Google: „Advertisements“/„Sponsored Links“, keine irreführenden Überschriften) [A3].
- Netzwerkcode erst nach Einwilligung einfügen. Ohne Einwilligung ist der Werbeplatz leer oder zeigt eine
  Eigenanzeige, nimmt aber dieselbe Höhe ein (kein Zusammenklappen, sonst Layoutverschiebung) [P1].
- Abstand zu Navigation und Buttons, damit niemand versehentlich klickt [A3]. Die Position „unter der Anleitung“ auf
  der Methodenseite liegt in der Nähe der Hinweis-Links: prüfen.
- Werbeplätze im gefilterten Zustand prüfen (siehe Abschnitt 2).

### Lighthouse-Ziel und Netzwerkprüfung

- PRD §9 Nr. 4 (Performance ≥ 90, Accessibility ≥ 95) und Nr. 5 gelten laut ADR 0001 verbindlich nur bei
  ausgeschalteter Werbung. Für den eingeschalteten Zustand fehlt ein Ziel; der Betreiber sollte es in #45 festlegen.
- Erwartung, **nicht belegt**: Ein Lauf ohne Einwilligung (Lighthouse klickt das Banner nicht weg) misst vor allem das
  Banner selbst. Mit Einwilligung kosten Anzeigen-Skripte Performance. Messen statt schätzen.
- `tools/netzwerk_pruefen.py` müsste Banner-Zustände unterscheiden: ohne Einwilligung keine Drittanfragen (bei K1, K4,
  K5 prüfbar, bei K2/K3 nicht erreichbar), mit Einwilligung erlaubte Ziele.

## Offene Punkte

1. **Lieferweg von Google „Privacy & messaging“ und Cookiebot:** Dass Skripte von Fremdservern kommen, ist naheliegend,
   aber nicht aus einer Primärquelle belegt (Cookiebot-Support: HTTP 403).
2. **CCM19:** Gilt die Google-Zertifizierung auch für die Download-Version, und ist das TCF-Modul im Starter-Tarif
   buchbar? Nur beim Anbieter zu klären.
3. **TCF-Version:** Google verlangt seit 01.03.2026 TC-Strings nach v2.3 [G6]. Cookiebot und CCM19 nennen auf ihren
   Seiten „TCF 2.4“; dazu wurde keine IAB-Quelle gefunden.
4. **Fallback-Banner von Google:** Ob es auf einer Seite mit nicht zertifiziertem Tool tatsächlich erscheint, folgert
   die Hilfeseite nur indirekt [G3].
5. **Kindgerichtete Inhalte:** Wie Google eine Website für Lehrkräfte mit Schulbezug einordnet, bleibt offen [A9].
6. **EthicalAds und Ezoic:** Die Hersteller-Seiten waren nicht abrufbar (DNS-Fehler); die Angaben stammen aus
   Suchtreffern und sind unbestätigt.
7. **Deutsche Vermarkter:** keine öffentlichen Aufnahmebedingungen; nur per Anfrage, die nicht Teil dieses Issues ist.
8. **K5:** Ob AdSense mit einem nicht zertifizierten Tool und Laden erst nach Einwilligung richtlinien- und
   rechtskonform ist, ist prüfbedürftig.
9. Barrierefreiheit von Klaro!/CookieConsent im eigenen Test prüfen (Tastatur, Screenreader, Kontrast in beiden
   Ansichten).

## Empfehlung (Vorschlag, die Entscheidung trifft der Betreiber in #45)

1. **Zuerst K1:** CookieConsent v3 (MIT, aktiv gepflegt, Fokusfalle, Texte selbst geschrieben) oder Klaro! (BSD-3,
   deutsche Texte und YouTube-Unterstützung eingebaut, aber seit 03/2025 keine Commits und offene
   Barrierefreiheits-Issues), selbst gehostet, zunächst nur für YouTube. Erfüllt ADR 0001 und 0003 vollständig.
   Optional selbst ausgelieferte Anzeigen oder Sponsoring ohne Fremdserver.
2. **Wenn Werbeeinnahmen nötig sind: K2** (AdSense + Google „Privacy & messaging“). Kostenlos, zertifiziert, kein
   eigener Server. Dafür müsste ADR 0001 bewusst geändert werden (Drittanfrage vor der Einwilligung bei
   eingeschalteter Werbung) und YouTube voraussichtlich weiter separat per Zwei-Klick laufen. **Prüfbedürftig.**
3. **Alternative, wenn ADR 0001 unverändert bleiben soll und ein PHP-Server möglich ist: K4** (CCM19 Download).
   Verlangt eine Änderung an ADR 0003, und Punkt 2 der offenen Punkte muss vorher geklärt sein.

## Quellen

Abgerufen am 2026-11-26.

**Google / AdSense**
- [G1] Google consent management requirements for serving ads in the EEA, the UK, and Switzerland – https://support.google.com/adsense/answer/13554116?hl=en
- [G2] Limited ads – https://support.google.com/adsense/answer/14210870?hl=en
- [G3] „Maximize message coverage“ and „Optimize consent message“ in Privacy & messaging – https://support.google.com/adsense/answer/18189118?hl=en
- [G4] Commonly asked questions about European regulations messages – https://support.google.com/adsense/answer/11546682?hl=en
- [G5] Liste zertifizierter CMPs: in [G1] enthalten
- [G6] Publisher integration with the IAB Europe TCF – https://support.google.com/adsense/answer/9804260 (nur Suchtreffer-Auszug: TC-Strings ab 01.03.2026 nach v2.3)
- [A1] Eligibility requirements for AdSense – https://support.google.com/adsense/answer/9724?hl=en
- [A2] More ads or paid promotional material than publisher-content – https://support.google.com/publisherpolicies/answer/11169917?hl=en
- [A3] Ad placement policies – https://support.google.com/adsense/answer/1346295?hl=en
- [A4] AdSense Program policies – https://support.google.com/adsense/answer/48182?hl=en
- [A5] Required content for privacy policies – https://support.google.com/adsense/answer/1348695?hl=en
- [A6] Payment thresholds – https://support.google.com/adsense/answer/1709871?hl=en
- [A7] Non-personalized ads – https://support.google.com/adsense/answer/9007336?hl=en
- [A8] Google Publisher Policies – https://support.google.com/adsense/answer/10502938?hl=en
- [A9] Tag a site or ad request for age restricted treatment – https://support.google.com/adsense/answer/3248194?hl=en
- [A10] EU user consent policy – https://www.google.com/about/company/user-consent-policy/
- [P1] Google Publisher Tag: Minimize layout shift – https://developers.google.com/publisher-tag/guides/minimize-layout-shift

**IAB Europe**
- [I1] CMP-Liste (JSON, `lastUpdated` 2026-11-19) – https://cmplist.consensu.org/v2/cmp-list.json (Webansicht https://iabeurope.eu/cmp-list/ lud die Tabelle nicht)
- [I2] TCF for CMPs – https://iabeurope.eu/tcf-for-cmps/

**Einwilligungs-Tools**
- [K1] Klaro! README und Lizenz – https://github.com/kiprotect/klaro (BSD-3; letzter Commit 2025-03-27, neuester Tag v0.7.22, per GitHub-API)
- [K2] Klaro! Übersetzungen – https://github.com/kiprotect/klaro/tree/master/src/translations
- [K3] Klaro! Issues #100, #503, #558 – https://github.com/kiprotect/klaro/issues?q=accessibility
- [K4] Klaro! Beispielkonfiguration – https://github.com/kiprotect/klaro/blob/master/dist/config.js
- [C1] CookieConsent Doku, Introduction – https://github.com/orestbida/cookieconsent/blob/master/docs/essential/introduction.md
- [C2] CookieConsent Repository und Release v3.3.0 – https://github.com/orestbida/cookieconsent
- [C3] CookieConsent Language Config – https://github.com/orestbida/cookieconsent/blob/master/docs/advanced/language-configuration.md
- [C4] CookieConsent Quelltext (`src/utils/focus-trap.js`, `data-buttons.js`) – https://github.com/orestbida/cookieconsent/tree/master/src/utils
- [C5] iframemanager README – https://github.com/orestbida/iframemanager
- [C6] CookieConsent Issue #562 – https://github.com/orestbida/cookieconsent/issues/562
- [X1] CCM19 Preise – https://www.ccm19.de/en/ccm19-prices.html
- [X2] CCM19 Systemvoraussetzungen – https://www.ccm19.de/en/faq/what-are-the-system-requirements.html
- [B1] Cookiebot Preise – https://www.cookiebot.com/en/pricing/

**Andere Netzwerke**
- [E1] EthicalAds Publisher-FAQ / Publisher-Seite – https://www.ethicalads.io/publishers/faq/ und https://www.ethicalads.io/publishers/ (**nicht abrufbar**, DNS-Fehler; Angaben aus Suchtreffer-Auszügen)
- [Z1] Ezoic Requirements / Incubator – https://support.ezoic.com/kb/article/getting-started-ezoics-requirements und https://www.ezoic.com/incubator (**nicht abrufbar**, DNS-Fehler; Angaben aus Suchtreffer-Auszügen)
- [N1] netpoint media – https://www.netpoint-media.de/ (Suche ergab keine Publisher-Aufnahmebedingungen)
- [M1] Media.net Inventory Policies – https://www.media.net/legal/programguidelines/ (nur Suchtreffer-Auszug)

**Gesetze und Behörden**
- [R1] § 25 TDDDG – https://www.gesetze-im-internet.de/ttdsg/__25.html
- [R3] § 5 DDG – https://www.gesetze-im-internet.de/ddg/__5.html
- [D1] DSK, Orientierungshilfe für Anbieter:innen von digitalen Diensten (OH Digitale Dienste), Version 1.2, Stand November 2024 – https://www.datenschutzkonferenz-online.de/media/oh/OH_Digitale_Dienste.pdf (Rn. 78, 84 f., 101, 122–126)
