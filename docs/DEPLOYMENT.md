# Deployment

Die Website ist statisch: `python build.py` erzeugt `dist/`, und dieser Ordner wird unverändert auf einen Webserver
kopiert. Ein Server-Backend, eine Datenbank oder PHP braucht es nicht.

## Voraussetzungen

- Webserver (z. B. Apache oder nginx) mit HTTPS, der einen Ordner als Webroot ausliefert.
- **Die Website muss im Wurzelverzeichnis einer (Sub-)Domain liegen**, z. B. `https://feedback.example.org/`, nicht unter
  `https://example.org/feedback/`. Alle Links beginnen mit `/`.
- Zugang per SSH mit Schlüssel (für `rsync` oder `sftp`). Ohne SSH-Zugang geht es auch mit einem SFTP-Programm von Hand,
  siehe unten.
- Lokal: Python-Umgebung wie in `AGENTS.md` unter „Befehle“.

## 1. Vorher: Konfiguration prüfen

In `config.yaml` steht noch ein Platzhalter, der vor dem ersten öffentlichen Upload ersetzt sein sollte:

| Feld | Stand | Issue |
|---|---|---|
| `kontakt_email` | `kontakt@example.org` | #58 |

`domain` ist optional und steht auf `https://feedback-tools.handrik.top` (#43). Sie erscheint im Fußtext jeder
Druckvorlage; leer gelassen steht dort nur der Website-Name.

Außerdem fehlen Impressum und Datenschutzerklärung noch (#44). Ohne sie sollte die Website nicht öffentlich erreichbar
sein. Das Skript warnt, solange `config.yaml` noch `example.org` enthält.

## 2. Bauen und prüfen

```bash
python build.py
pytest
```

Beides muss fehlerfrei laufen. Danach liegt die fertige Website in `dist/`. Mit `python build.py --serve` lässt sie sich
vorher lokal ansehen.

## 3. Hochladen mit dem Skript (empfohlen)

Einmalig einrichten:

1. `deploy.env.beispiel` nach `deploy.env` kopieren. `deploy.env` wird von Git ignoriert.
2. In `deploy.env` `DEPLOY_ZIEL` auf `benutzer@server:/pfad/zum/webroot` setzen, bei Bedarf `DEPLOY_PORT` und
   `DEPLOY_SCHLUESSEL`.
3. Prüfen, dass die Anmeldung ohne Passwort klappt: `ssh benutzer@server`.

Statt `deploy.env` gehen auch Umgebungsvariablen mit denselben Namen; eine andere Datei wählt `DEPLOY_ENV=pfad`.

Dann in Git Bash, WSL, Linux oder macOS im Repo-Ordner:

```bash
tools/deploy.sh --probe   # bauen, testen und nur anzeigen, was sich ändern würde
tools/deploy.sh           # bauen, testen und hochladen
```

Das Skript baut neu, lässt die Tests laufen und bricht bei einem Fehler ab, bevor etwas hochgeladen wird.

### rsync oder sftp

- **`rsync`** (Standard): überträgt nur Geändertes und **löscht auf dem Server, was nicht mehr in `dist/` ist**. Der
  Zielordner darf darum nur die Website enthalten. rsync muss lokal und auf dem Server installiert sein. Git Bash
  bringt es nicht mit; unter Windows dann WSL nutzen oder `DEPLOY_METHODE="sftp"`.
- **`sftp`**: lädt alles hoch und überschreibt vorhandene Dateien, **löscht aber nichts**. Fällt eine Seite weg (z. B.
  eine Methode wird entfernt oder umbenannt), bleibt die alte Datei auf dem Server erreichbar. Sie muss von Hand
  gelöscht werden, oder man leert den Zielordner vor dem Upload.

## 4. Hochladen von Hand (ohne Skript)

Mit einem SFTP-Programm (z. B. WinSCP, FileZilla) den **Inhalt** von `dist/` (nicht den Ordner selbst) in den Webroot
kopieren. In WinSCP räumt „Synchronisieren“ mit der Option „Löschen“ auch alte Dateien weg.

## 5. Webserver einrichten

- **Fehlerseite:** `404.html` liegt im Wurzelverzeichnis und muss als Seite für „nicht gefunden“ eingetragen werden.
  - Apache (`.htaccess` oder vHost): `ErrorDocument 404 /404.html`
  - nginx: `error_page 404 /404.html;`
- **Verzeichnisseiten:** Jede Seite ist `<pfad>/index.html`. Der Server muss `index.html` als Startdatei eines Ordners
  ausliefern (bei Apache und nginx Standard).
- **Zwischenspeicher:** Dateinamen enthalten keine Versionsnummer (`/static/css/site.css`). Darum keine langen
  Cache-Zeiten für `/static/css/` und `/static/js/` setzen, sonst sehen Besucher nach einem Update altes CSS. Für
  `/static/fonts/` sind lange Cache-Zeiten unbedenklich.
- **Datenschutz:** Die Website setzt keine Cookies und lädt nichts von fremden Servern. Der Webserver selbst schreibt
  aber meist Zugriffsprotokolle mit IP-Adressen. Was dort gespeichert wird und wie lange, gehört in die
  Datenschutzerklärung (#44); am einfachsten IP-Adressen kürzen oder Protokolle nach wenigen Tagen löschen.

## 6. Nach dem Upload prüfen

- Startseite, eine Methode, eine Druckvorlage und eine unbekannte Adresse (soll die eigene 404-Seite zeigen) aufrufen.
- Im Browser unter Entwicklerwerkzeuge → Netzwerk: Alle Anfragen gehen an die eigene Domain.
- Beide Ansichten (Pinnwand/Klar) einmal umschalten.
