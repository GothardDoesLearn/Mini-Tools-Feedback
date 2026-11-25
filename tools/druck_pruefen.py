"""Druckprüfung mit Headless-Edge/Chrome (nur Standardbibliothek).

Baut die Seite in einen temporären Ordner, liefert sie lokal (127.0.0.1) aus und druckt
Druckvorlagen als PDF bzw. macht Bildschirmfotos. Kontaktiert keine Drittserver.

  python tools/druck_pruefen.py feedback-hand ampelkarten
  python tools/druck_pruefen.py --alle
  python tools/druck_pruefen.py --screenshot /vorlagen/ --breite 375 --ansicht klar --out bilder
"""

import argparse
import functools
import html
import http.server
import io
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import urllib.parse
import zlib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRUCKVORLAGEN_YAML = ROOT / "content" / "druckvorlagen.yaml"
ANSICHT_SCHLUESSEL = "mt-ansicht"  # wie in templates/ansicht.js
ANSICHTEN = ("pinnwand", "klar")

BROWSER_KANDIDATEN = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]
BROWSER_BEFEHLE = [
    "microsoft-edge",
    "microsoft-edge-stable",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "msedge",
    "chrome",
]
# Hintergrund-Dienste des Browsers abschalten, damit nichts nach außen telefoniert.
BROWSER_ARGS = [
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-sync",
    "--disable-extensions",
    "--disable-default-apps",
    "--metrics-recording-only",
    "--safebrowsing-disable-auto-update",
    "--hide-scrollbars",
]


# ---------- reine Funktionen (getestet) ----------


def erwartete_seiten(text: str) -> tuple[int, int] | None:
    """Liest die führende Zahl oder Spanne aus dem Freitext `seiten` („3 (je Farbe 1)“, „1–2“)."""
    m = re.match(r"\s*(\d+)(?:\s*[-–]\s*(\d+))?", text or "")
    if not m:
        return None
    von = int(m.group(1))
    bis = int(m.group(2)) if m.group(2) else von
    return (min(von, bis), max(von, bis))


def lies_druckvorlagen(text: str) -> dict[str, str]:
    """id -> seiten-Text aus content/druckvorlagen.yaml (Zeilenformat, ohne YAML-Paket)."""
    ergebnis: dict[str, str] = {}
    aktuelle: str | None = None
    for zeile in text.splitlines():
        m = re.match(r"^-\s+id:\s*['\"]?([^'\"\s]+)", zeile)
        if m:
            aktuelle = m.group(1)
            ergebnis[aktuelle] = ""
            continue
        m = re.match(r"^\s+seiten:\s*(.*)$", zeile)
        if m and aktuelle:
            ergebnis[aktuelle] = m.group(1).strip().strip("'\"")
    return ergebnis


_OBJ = re.compile(rb"(\d+)\s+\d+\s+obj\b(.*?)endobj", re.DOTALL)
_TYP_SEITE = re.compile(rb"/Type\s*/Page(?![a-zA-Z])")
_TYP_SEITEN = re.compile(rb"/Type\s*/Pages\b")
_MEDIABOX = re.compile(rb"/MediaBox\s*\[\s*([-\d.\s]+?)\s*\]")
_PARENT = re.compile(rb"/Parent\s+(\d+)\s+\d+\s+R")
_KIDS = re.compile(rb"/Kids\s*\[([^\]]*)\]")


def pdf_seiten(daten: bytes) -> list[str]:
    """Ausrichtung je Seite ('hoch'/'quer') in Seitenreihenfolge (Seitenobjekte)."""
    objekte = {int(m.group(1)): m.group(2) for m in _OBJ.finditer(daten)}

    def mediabox(nr: int, tiefe: int = 0) -> list[float] | None:
        inhalt = objekte.get(nr, b"")
        m = _MEDIABOX.search(inhalt)
        if m:
            return [float(x) for x in m.group(1).split()]
        p = _PARENT.search(inhalt)
        return mediabox(int(p.group(1)), tiefe + 1) if p and tiefe < 20 else None

    def blaetter(nr: int, tiefe: int = 0) -> list[int]:
        inhalt = objekte.get(nr, b"")
        if _TYP_SEITEN.search(inhalt):
            k = _KIDS.search(inhalt)
            kinder = [int(x) for x in re.findall(rb"(\d+)\s+\d+\s+R", k.group(1))] if k else []
            return [s for kind in kinder for s in blaetter(kind, tiefe + 1)] if tiefe < 20 else []
        return [nr] if _TYP_SEITE.search(inhalt) else []

    wurzeln = [
        nr for nr, inh in objekte.items() if _TYP_SEITEN.search(inh) and not _PARENT.search(inh)
    ]
    seiten = [s for w in wurzeln for s in blaetter(w)]
    if not seiten:
        seiten = [nr for nr, inh in objekte.items() if _TYP_SEITE.search(inh)]

    ergebnis = []
    for nr in seiten:
        box = mediabox(nr)
        if box and len(box) == 4:
            breite, hoehe = abs(box[2] - box[0]), abs(box[3] - box[1])
            ergebnis.append("quer" if breite > hoehe else "hoch")
        else:
            ergebnis.append("?")
    return ergebnis


def ansicht_einfuegen(html: bytes, ansicht: str) -> bytes:
    """Setzt die Ansicht im localStorage, bevor ansicht.js sie liest (Skript direkt nach <head>)."""
    skript = (
        f'<script>try{{localStorage.setItem("{ANSICHT_SCHLUESSEL}","{ansicht}")}}'
        f"catch(e){{}}</script>"
    ).encode()
    return re.sub(rb"(<head\b[^>]*>)", lambda m: m.group(1) + skript, html, count=1)


_PNG_SIGNATUR = b"\x89PNG\r\n\x1a\n"


def _png_chunk(typ: bytes, daten: bytes) -> bytes:
    crc = zlib.crc32(typ + daten) & 0xFFFFFFFF
    return struct.pack(">I", len(daten)) + typ + daten + struct.pack(">I", crc)


def png_zuschneiden(daten: bytes, breite: int, hoehe: int) -> bytes:
    """Schneidet ein 8-Bit-RGB(A)-PNG auf die linke obere Ecke breite×hoehe zu."""
    if not daten.startswith(_PNG_SIGNATUR):
        raise ValueError("kein PNG")
    pos, idat, ihdr = 8, b"", b""
    while pos < len(daten):
        laenge = struct.unpack(">I", daten[pos : pos + 4])[0]
        typ, inhalt = daten[pos + 4 : pos + 8], daten[pos + 8 : pos + 8 + laenge]
        if typ == b"IHDR":
            ihdr = inhalt
        elif typ == b"IDAT":
            idat += inhalt
        pos += 12 + laenge
    w, h, tiefe, farbtyp, _, _, interlace = struct.unpack(">IIBBBBB", ihdr)
    if tiefe != 8 or farbtyp not in (2, 6) or interlace:
        raise ValueError("nur 8-Bit-RGB/RGBA ohne Interlacing")
    bpp = 3 if farbtyp == 2 else 4
    zeile = w * bpp
    roh = zlib.decompress(idat)
    neu_b, neu_h = min(breite, w), min(hoehe, h)
    vorher = bytearray(zeile)
    ausgabe = bytearray()
    for y in range(neu_h):
        filt = roh[y * (zeile + 1)]
        akt = bytearray(roh[y * (zeile + 1) + 1 : (y + 1) * (zeile + 1)])
        for i in range(zeile):
            a = akt[i - bpp] if i >= bpp else 0
            b = vorher[i]
            c = vorher[i - bpp] if i >= bpp else 0
            if filt == 1:
                akt[i] = (akt[i] + a) & 0xFF
            elif filt == 2:
                akt[i] = (akt[i] + b) & 0xFF
            elif filt == 3:
                akt[i] = (akt[i] + (a + b) // 2) & 0xFF
            elif filt == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                vorhersage = a if pa <= pb and pa <= pc else b if pb <= pc else c
                akt[i] = (akt[i] + vorhersage) & 0xFF
        ausgabe += b"\x00" + akt[: neu_b * bpp]
        vorher = akt
    kopf = struct.pack(">IIBBBBB", neu_b, neu_h, 8, farbtyp, 0, 0, 0)
    return (
        _PNG_SIGNATUR
        + _png_chunk(b"IHDR", kopf)
        + _png_chunk(b"IDAT", zlib.compress(bytes(ausgabe), 9))
        + _png_chunk(b"IEND", b"")
    )


# ---------- Browser, Server, Build ----------


class Fehler(Exception):
    pass


def finde_browser(angegeben: str | None) -> str:
    if angegeben:
        if Path(angegeben).is_file():
            return angegeben
        raise Fehler(f"Browser nicht gefunden: {angegeben}")
    for pfad in BROWSER_KANDIDATEN:
        if pfad and Path(pfad).is_file():
            return pfad
    for befehl in BROWSER_BEFEHLE:
        gefunden = shutil.which(befehl)
        if gefunden:
            return gefunden
    raise Fehler(
        "Kein Microsoft Edge oder Google Chrome/Chromium gefunden. "
        "Bitte einen der Browser installieren oder den Pfad mit --browser PFAD angeben."
    )


def baue(ziel: Path) -> None:
    lauf = subprocess.run(
        [sys.executable, str(ROOT / "build.py"), "--out", str(ziel)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if lauf.returncode != 0:
        raise Fehler(f"Build fehlgeschlagen:\n{lauf.stdout}{lauf.stderr}")


@dataclass
class Server:
    httpd: http.server.ThreadingHTTPServer

    @property
    def basis(self) -> str:
        return f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def rahmen_html(ziel: str, breite: int, hoehe: int) -> bytes:
    """Seite mit einem iframe in exakter Breite: Headless-Fenster sind mindestens ~500 px breit."""
    ziel = html.escape(ziel, quote=True)
    return (
        "<!doctype html><meta charset=utf-8><style>html,body{margin:0;background:#fff}"
        f"iframe{{display:block;border:0;width:{breite}px;height:{hoehe}px}}</style>"
        f'<iframe src="{ziel}"></iframe>'
    ).encode()


RAHMEN_PFAD = "/__rahmen"


def starte_server(ordner: Path, ansicht: str | None) -> Server:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):  # still
            pass

        def _sende(self, daten: bytes) -> io.BytesIO:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(daten)))
            self.end_headers()
            return io.BytesIO(daten)

        def send_head(self):
            teile = urllib.parse.urlsplit(self.path)
            if teile.path == RAHMEN_PFAD:
                q = urllib.parse.parse_qs(teile.query)
                return self._sende(
                    rahmen_html(q["ziel"][0], int(q["breite"][0]), int(q["hoehe"][0]))
                )
            pfad = Path(self.translate_path(self.path))
            if ansicht and pfad.is_dir() and teile.path.endswith("/"):
                pfad = pfad / "index.html"
            if ansicht and pfad.suffix == ".html" and pfad.is_file():
                return self._sende(ansicht_einfuegen(pfad.read_bytes(), ansicht))
            return super().send_head()

    handler = functools.partial(Handler, directory=str(ordner))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return Server(httpd)


def browser_lauf(browser: str, profil: Path, args: list[str], url: str) -> None:
    befehl = [browser, *BROWSER_ARGS, f"--user-data-dir={profil}", *args, url]
    lauf = subprocess.run(befehl, capture_output=True, text=True, timeout=120)
    if lauf.returncode != 0:
        raise Fehler(f"Browser-Aufruf fehlgeschlagen ({lauf.returncode}):\n{lauf.stderr[-2000:]}")


def drucke_pdf(browser: str, profil: Path, url: str, ziel: Path) -> bytes:
    browser_lauf(browser, profil, ["--no-pdf-header-footer", f"--print-to-pdf={ziel}"], url)
    if not ziel.is_file():
        raise Fehler(f"Keine PDF erzeugt für {url}")
    return ziel.read_bytes()


def screenshot(
    browser: str, profil: Path, server: Server, pfad: str, ziel: Path, breite: int, hoehe: int
) -> None:
    query = urllib.parse.urlencode(
        {"ziel": "/" + pfad.lstrip("/"), "breite": breite, "hoehe": hoehe}
    )
    fenster = f"--window-size={max(breite, 800) + 50},{hoehe + 300}"
    browser_lauf(
        browser,
        profil,
        [fenster, "--force-device-scale-factor=1", f"--screenshot={ziel}"],
        f"{server.basis}{RAHMEN_PFAD}?{query}",
    )
    if not ziel.is_file():
        raise Fehler(f"Kein Bildschirmfoto erzeugt für {pfad}")
    ziel.write_bytes(png_zuschneiden(ziel.read_bytes(), breite, hoehe))


# ---------- Ablauf ----------


def pruefe_vorlagen(browser: str, ids: list[str], tmp: Path, server: Server) -> int:
    erwartet = lies_druckvorlagen(DRUCKVORLAGEN_YAML.read_text(encoding="utf-8"))
    unbekannt = [i for i in ids if i not in erwartet]
    if unbekannt:
        raise Fehler(f"Unbekannte Druckvorlage(n): {', '.join(unbekannt)}")
    abweichungen = 0
    for vid in ids:
        seiten = pdf_seiten(
            drucke_pdf(
                browser, tmp / "profil", f"{server.basis}/vorlagen/{vid}/", tmp / f"{vid}.pdf"
            )
        )
        spanne = erwartete_seiten(erwartet[vid])
        ausrichtung = ", ".join(seiten)
        if spanne is None:
            urteil = f"ohne Sollwert ({erwartet[vid] or 'leer'})"
        elif spanne[0] <= len(seiten) <= spanne[1]:
            urteil = "ok"
        else:
            urteil = f"ABWEICHUNG, erwartet {erwartet[vid]}"
            abweichungen += 1
        print(f"{vid}: {len(seiten)} Seite(n) [{ausrichtung}] – {urteil}")
    print(f"{len(ids)} Vorlage(n) geprüft, {abweichungen} Abweichung(en).")
    return 1 if abweichungen else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Druckvorlagen per Headless-Edge/Chrome prüfen oder Bildschirmfotos machen."
    )
    parser.add_argument("vorlagen", nargs="*", metavar="VORLAGE-ID")
    parser.add_argument("--alle", action="store_true", help="alle Druckvorlagen prüfen")
    parser.add_argument("--browser", metavar="PFAD", help="Pfad zu Edge/Chrome")
    parser.add_argument(
        "--screenshot", action="append", default=[], metavar="URL-PFAD", help="z. B. /methoden/"
    )
    parser.add_argument("--breite", action="append", type=int, default=[], metavar="PX")
    parser.add_argument("--hoehe", type=int, default=1600, metavar="PX")
    parser.add_argument("--ansicht", choices=ANSICHTEN, help="Ansicht für Bildschirmfotos")
    parser.add_argument("--out", type=Path, default=Path("druck-pruefung"), help="Ordner für PNGs")
    args = parser.parse_args(argv)

    if not (args.vorlagen or args.alle or args.screenshot):
        parser.error("Vorlage-ID(s), --alle oder --screenshot angeben.")

    try:
        browser = finde_browser(args.browser)
        with tempfile.TemporaryDirectory(prefix="druck_pruefen_") as t:
            tmp = Path(t)
            baue(tmp / "site")
            code = 0
            if args.vorlagen or args.alle:
                ids = args.vorlagen
                if args.alle:
                    ids = list(lies_druckvorlagen(DRUCKVORLAGEN_YAML.read_text(encoding="utf-8")))
                server = starte_server(tmp / "site", None)
                try:
                    code = pruefe_vorlagen(browser, ids, tmp, server)
                finally:
                    server.stop()
            if args.screenshot:
                args.out.mkdir(parents=True, exist_ok=True)
                server = starte_server(tmp / "site", args.ansicht)
                try:
                    for pfad in args.screenshot:
                        for breite in args.breite or [1280]:
                            name = re.sub(r"[^a-zA-Z0-9]+", "_", pfad).strip("_") or "start"
                            datei = args.out / f"{name}_{args.ansicht or 'standard'}_{breite}.png"
                            screenshot(
                                browser,
                                tmp / "profil",
                                server,
                                pfad,
                                datei.resolve(),
                                breite,
                                args.hoehe,
                            )
                            print(f"Gespeichert: {datei}")
                finally:
                    server.stop()
            return code
    except Fehler as fehler:
        print(f"Fehler: {fehler}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
