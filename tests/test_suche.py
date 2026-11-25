"""Volltextsuche (Issue #18): JSON-Suchindex aus dem Build + Suchfeld in static/js/filter.js."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from generator import paths
from generator.build import build
from generator.content import load_site
from generator.suche import suchindex

NODE = shutil.which("node")
BOX = r'<input type="checkbox" name="([a-z]+)" value="([a-z-]+)"'
INDEX = r"<script type=\"application/json\" data-suchindex>(.*?)</script>"
braucht_node = pytest.mark.skipif(NODE is None, reason="Node.js nicht installiert")


@pytest.fixture(scope="module")
def startseite(tmp_path_factory) -> str:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return (out / "index.html").read_text(encoding="utf-8")


# --- Index (Python) ---------------------------------------------------------------------------


def test_index_enthaelt_titel_aliase_und_anleitung_als_klartext():
    site = load_site(paths.CONTENT_DIR)
    eintraege = {e["id"]: e for e in suchindex(site)}
    assert set(eintraege) == {m.id for m in site.methoden}
    hand = eintraege["5-finger-methode"]
    assert hand["titel"] == "5-Finger-Methode"
    assert hand["aliase"] == ["Feedback-Hand", "Hand 5-Finger"]
    assert "Jeder Finger steht für einen Aspekt" in hand["text"]
    for eintrag in eintraege.values():
        assert "<" not in eintrag["text"] and "##" not in eintrag["text"]
        assert "  " not in eintrag["text"] and "\n" not in eintrag["text"]


def test_startseite_bettet_den_index_als_json_ein(startseite: str):
    (roh,) = re.findall(INDEX, startseite, re.S)
    daten = json.loads(roh)
    karten_ids = re.findall(r'<article class="karte"[^>]*data-methode="([^"]+)"', startseite)
    assert {e["id"] for e in daten} == set(karten_ids)


def test_suchfeld_steht_in_den_startaktionen_mit_label(startseite: str):
    aktionen = re.search(r'<div class="startaktionen">(.*?)</div>\s*<section', startseite, re.S)
    assert aktionen
    feld = re.search(r'<input [^>]*type="search"[^>]*>', aktionen.group(1))
    assert feld and "data-suche" in feld.group(0)
    feld_id = re.search(r'id="([^"]+)"', feld.group(0)).group(1)
    assert re.search(rf'<label [^>]*for="{feld_id}"[^>]*>\s*\S', aktionen.group(1))


# --- Verhalten (Node + Mini-DOM) --------------------------------------------------------------

# Schritte: {"tippen": text} | {"klick": id} | {"reset": true} | {"zurueck": search}
STUB = r"""
const fs = require("fs");
const eingabe = JSON.parse(fs.readFileSync(0, "utf8"));
function element(attrs) {
  const a = Object.assign({}, attrs);
  const listener = {};
  return {
    hidden: false, textContent: "", checked: false, value: "",
    getAttribute: (k) => (k in a ? a[k] : null),
    setAttribute: (k, v) => { a[k] = String(v); },
    hasAttribute: (k) => k in a,
    addEventListener: (t, f) => { (listener[t] = listener[t] || []).push(f); },
    feuern: (t, e) => (listener[t] || []).forEach((f) => f(e || { preventDefault() {} })),
  };
}
const boxen = eingabe.boxen.map(([name, value]) => Object.assign(
  element({ type: "checkbox" }), { name, value, type: "checkbox" }));
const formular = element({ "data-filterleiste": "" });
formular.querySelectorAll = () => boxen;
const knoepfe = eingabe.kategorien.map((id, i) =>
  element({ "data-kategorie": id, "aria-pressed": i === 0 ? "true" : "false" }));
const karten = Object.entries(eingabe.karten).map(([id, kat]) =>
  element({ "data-methode": id, "data-filter-kategorie": kat }));
const suchfeld = element({ "data-suche": "" });
const index = element({ "data-suchindex": "" });
index.textContent = eingabe.index;
const document = {
  querySelector: (s) => ({ "[data-filterleiste]": formular, "[data-suche]": suchfeld,
                            "[data-suchindex]": index })[s] || null,
  querySelectorAll: (s) => ({ "[data-methode]": karten, "[data-kategorie]": knoepfe })[s] || [],
};
const verlauf = [];
const fensterListener = {};
const location = { pathname: "/", search: eingabe.search, hash: "", assign() {} };
function setzen(art, url) {
  verlauf.push([art, url]);
  const i = url.indexOf("?");
  location.search = i === -1 ? "" : url.slice(i);
}
const window = {
  setTimeout: (f) => f(), location,
  history: { pushState: (s, t, url) => setzen("push", url),
             replaceState: (s, t, url) => setzen("replace", url) },
  addEventListener: (t, f) => { (fensterListener[t] = fensterListener[t] || []).push(f); },
};
function zustand() {
  return {
    sichtbar: karten.filter((k) => !k.hidden).map((k) => k.getAttribute("data-methode")),
    feld: suchfeld.value,
    search: location.search,
    verlauf: verlauf.splice(0),
  };
}
new Function("document", "window", "setTimeout", "module",
  fs.readFileSync(eingabe.skript, "utf8"))(document, window, window.setTimeout, undefined);
const ergebnisse = [zustand()];
for (const schritt of eingabe.schritte) {
  if ("tippen" in schritt) {
    suchfeld.value = schritt.tippen;
    suchfeld.feuern("input");
  } else if ("klick" in schritt) {
    knoepfe.find((k) => k.getAttribute("data-kategorie") === schritt.klick).feuern("click");
  } else if ("reset" in schritt) {
    formular.feuern("reset");
  } else if ("zurueck" in schritt) {
    location.search = schritt.zurueck;
    (fensterListener.popstate || []).forEach((f) => f({}));
  }
  ergebnisse.push(zustand());
}
process.stdout.write(JSON.stringify(ergebnisse));
"""


def _laufen(startseite: str, search: str = "", schritte: list[dict] | None = None) -> list[dict]:
    karten = dict(
        re.findall(
            r'<article class="karte"[^>]*?data-methode="([^"]+)"[^>]*?'
            r'data-filter-kategorie="([^"]*)"',
            startseite,
        )
    )
    eingabe = {
        "skript": str(Path("static/js/filter.js").resolve()),
        "karten": karten,
        "boxen": re.findall(BOX, startseite),
        "kategorien": re.findall(r'<button [^>]*data-kategorie="([^"]*)"', startseite),
        "index": re.search(INDEX, startseite, re.S).group(1),
        "search": search,
        "schritte": schritte or [],
    }
    assert len(karten) == 31
    r = subprocess.run(
        [NODE, "-e", STUB],
        input=json.dumps(eingabe),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(r.stdout)


@braucht_node
def test_suche_hand_findet_die_5_finger_methode(startseite: str):
    e = _laufen(startseite, "", [{"tippen": "Hand"}])[-1]
    assert "5-finger-methode" in e["sichtbar"]
    assert len(e["sichtbar"]) < 31


@braucht_node
def test_suche_ueber_aliase(startseite: str):
    e = _laufen(startseite, "", [{"tippen": "kummerkasten"}])[-1]
    assert e["sichtbar"] == ["briefkasten"]


@braucht_node
def test_suche_ignoriert_gross_klein_und_akzente_und_verlangt_alle_woerter(startseite: str):
    gross, zwei_woerter, unsinn = _laufen(
        startseite,
        "",
        [{"tippen": "FRAGEBOGEN"}, {"tippen": "  feedback   hand "}, {"tippen": "xyzxyz"}],
    )[1:]
    assert "fragebogen" in gross["sichtbar"]
    assert "5-finger-methode" in zwei_woerter["sichtbar"]
    assert unsinn["sichtbar"] == []


@braucht_node
def test_tippen_ersetzt_die_url_statt_verlaufseintraege(startseite: str):
    h, ha = _laufen(startseite, "", [{"tippen": "H"}, {"tippen": "Ha"}])[1:]
    assert h["verlauf"] == [["replace", "/?suche=H"]]
    assert ha["verlauf"] == [["replace", "/?suche=Ha"]]


@braucht_node
def test_suchbegriff_im_link_wird_wiederhergestellt(startseite: str):
    (e,) = _laufen(startseite, "?suche=Feedback%20Hand")
    assert e["feld"] == "Feedback Hand"
    assert "5-finger-methode" in e["sichtbar"]
    assert e["verlauf"] == []
    # Komma bleibt Teil des Suchbegriffs
    (k,) = _laufen(startseite, "?suche=a%2Cb")
    assert k["feld"] == "a,b"


@braucht_node
def test_suche_kombiniert_mit_kategorie(startseite: str):
    e = _laufen(startseite, "?suche=Hand", [{"klick": "B"}])[-1]
    assert "5-finger-methode" not in e["sichtbar"]  # Kategorie A
    assert e["search"] == "?suche=Hand&kategorie=B" or e["search"] == "?kategorie=B&suche=Hand"


@braucht_node
def test_zuruecksetzen_und_zurueck_leeren_das_suchfeld(startseite: str):
    nach_reset = _laufen(startseite, "?suche=Hand", [{"reset": True}])[-1]
    assert nach_reset["feld"] == ""
    assert len(nach_reset["sichtbar"]) == 31
    nach_zurueck = _laufen(startseite, "?suche=Hand", [{"zurueck": ""}])[-1]
    assert nach_zurueck["feld"] == ""
    assert len(nach_zurueck["sichtbar"]) == 31
