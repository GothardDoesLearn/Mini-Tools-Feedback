"""Netzwerkprüfung mit Headless-Edge/Chrome (PRD §9.5, Issue #38; nur Standardbibliothek).

Baut die Seite in einen temporären Ordner, liefert sie lokal (127.0.0.1) aus und öffnet jede
HTML-Seite in beiden Ansichten. Ein eingeschleustes Messskript liest nach dem Laden alle
Ressourcen der Seite aus (Resource Timing: Stylesheets, Skripte, Schriften, Bilder, fetch).
Jede Ressource, die nicht von 127.0.0.1 kommt, ist ein Befund. Es wird nichts angeklickt:
Videos (Zwei-Klick-Einbettung) bleiben ungestartet, Werbung ist im Build aus.

  python tools/netzwerk_pruefen.py
  python tools/netzwerk_pruefen.py /methoden/daumenprobe/ --ansicht klar
"""

import argparse
import functools
import html
import http.server
import io
import json
import re
import subprocess
import sys
import tempfile
import threading
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.druck_pruefen import (  # noqa: E402 (Pfad oben gesetzt)
    ANSICHTEN,
    BROWSER_ARGS,
    Fehler,
    Server,
    ansicht_einfuegen,
    baue,
    finde_browser,
)

MESS_ID = "__netzwerk"
# Wartet nach dem Laden kurz (späte Anfragen, z. B. Schriften), dann Liste ins DOM schreiben.
MESSSKRIPT = (
    "<script>addEventListener('load',function(){setTimeout(function(){"
    "var p=document.createElement('pre');p.id='" + MESS_ID + "';"
    "p.textContent=JSON.stringify(performance.getEntriesByType('resource')"
    ".map(function(e){return e.name}));document.body.appendChild(p)},500)})</script>"
)


# ---------- reine Funktionen (getestet) ----------


def messskript_einfuegen(html_bytes: bytes) -> bytes:
    """Setzt das Messskript direkt hinter <head>, damit es vor allen anderen Skripten läuft."""
    return re.sub(
        rb"(<head\b[^>]*>)", lambda m: m.group(1) + MESSSKRIPT.encode(), html_bytes, count=1
    )


def gemessene_urls(dom: str) -> list[str]:
    """Liest die Liste des Messskripts aus dem DOM (Ausgabe von --dump-dom)."""
    treffer = re.search(rf'<pre id="{MESS_ID}">(.*?)</pre>', dom, re.S)
    if not treffer:
        raise Fehler("Messskript hat keine Liste geschrieben (Seite nicht fertig geladen?)")
    return json.loads(html.unescape(treffer.group(1)))


def fremde_urls(urls: list[str], basis: str) -> list[str]:
    """Alle URLs, die nicht vom lokalen Server (Schema + Host + Port von `basis`) kommen."""

    def herkunft(url: str) -> tuple[str, str]:
        teile = urllib.parse.urlsplit(url)
        return teile.scheme, teile.netloc

    return [u for u in urls if herkunft(u) != herkunft(basis)]


def seitenpfade(ordner: Path) -> list[str]:
    """URL-Pfade aller HTML-Seiten im Build (…/index.html -> …/)."""
    pfade = []
    for datei in sorted(ordner.rglob("*.html")):
        rel = datei.relative_to(ordner).as_posix()
        pfade.append("/" + (rel.removesuffix("index.html") if rel.endswith("index.html") else rel))
    return pfade


# ---------- Browser, Server ----------


def starte_server(ordner: Path, ansicht: str) -> Server:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):  # still
            pass

        def send_head(self):
            pfad = Path(self.translate_path(self.path))
            if pfad.is_dir():
                pfad = pfad / "index.html"
            if pfad.suffix != ".html" or not pfad.is_file():
                return super().send_head()
            daten = messskript_einfuegen(ansicht_einfuegen(pfad.read_bytes(), ansicht))
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(daten)))
            self.end_headers()
            return io.BytesIO(daten)

    handler = functools.partial(Handler, directory=str(ordner))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return Server(httpd)


def lade_dom(browser: str, profil: Path, url: str) -> str:
    befehl = [
        browser,
        *BROWSER_ARGS,
        f"--user-data-dir={profil}",
        "--dump-dom",
        "--virtual-time-budget=5000",
        url,
    ]
    lauf = subprocess.run(
        befehl, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120
    )
    if lauf.returncode != 0:
        raise Fehler(f"Browser-Aufruf fehlgeschlagen ({lauf.returncode}):\n{lauf.stderr[-2000:]}")
    return lauf.stdout


# ---------- Ablauf ----------


def pruefe(browser: str, site: Path, tmp: Path, pfade: list[str], ansichten: list[str]) -> int:
    befunde = 0
    ressourcen = 0
    for ansicht in ansichten:
        server = starte_server(site, ansicht)
        try:
            for pfad in pfade:
                urls = gemessene_urls(lade_dom(browser, tmp / "profil", server.basis + pfad))
                ressourcen += len(urls)
                for url in fremde_urls(urls, server.basis):
                    befunde += 1
                    print(f"BEFUND {ansicht} {pfad}: {url}")
        finally:
            server.stop()
    print(
        f"{len(pfade)} Seite(n) × {len(ansichten)} Ansicht(en) geprüft, "
        f"{ressourcen} Ressourcen geladen, {befunde} Anfrage(n) an Drittserver."
    )
    return 1 if befunde else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prüft per Headless-Edge/Chrome, dass keine Seite Drittserver anfragt."
    )
    parser.add_argument("pfade", nargs="*", metavar="URL-PFAD", help="Standard: alle Seiten")
    parser.add_argument("--browser", metavar="PFAD", help="Pfad zu Edge/Chrome")
    parser.add_argument("--ansicht", choices=ANSICHTEN, help="Standard: beide Ansichten")
    args = parser.parse_args(argv)

    try:
        browser = finde_browser(args.browser)
        with tempfile.TemporaryDirectory(prefix="netzwerk_pruefen_") as t:
            tmp = Path(t)
            baue(tmp / "site")
            pfade = args.pfade or seitenpfade(tmp / "site")
            ansichten = [args.ansicht] if args.ansicht else list(ANSICHTEN)
            return pruefe(browser, tmp / "site", tmp, pfade, ansichten)
    except Fehler as fehler:
        print(f"Fehler: {fehler}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
