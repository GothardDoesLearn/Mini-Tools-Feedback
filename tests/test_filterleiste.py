"""Filterleiste auf der Startseite (Issue #14): Gruppen aus filter.yaml, data-* an den Karten."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from generator.build import build
from generator.css import stylesheet

# Stundenende + Analog + Mit Druckvorlage (von Hand aus content/ ermittelt). wimmelbild-zuordnen
# fehlt, weil seine Druckvorlage den Status „platzhalter“ hat (PRD §9.3).
STUNDENENDE_ANALOG_MIT_VORLAGE = {
    "5-finger-methode",
    "aufstellung",
    "exit-ticket",
    "klebepunkte",
    "reflexionskarten",
    "reflexionswuerfel",
    "smileys",
    "wetterbericht",
    "zielscheibe",
}


@pytest.fixture(scope="module")
def dist(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return out


@pytest.fixture(scope="module")
def startseite(dist: Path) -> str:
    return (dist / "index.html").read_text(encoding="utf-8")


def _karten_daten(html: str) -> dict[str, dict[str, set[str]]]:
    """Methoden-ID -> {feld: {werte}} aus den data-filter-*-Attributen der Karten."""
    daten = {}
    for tag in re.findall(r'<article class="karte"[^>]*>', html):
        attrs = dict(re.findall(r'data-filter-([a-z]+)="([^"]*)"', tag))
        methoden_id = re.search(r'data-methode="([^"]+)"', tag).group(1)
        daten[methoden_id] = {feld: set(werte.split()) for feld, werte in attrs.items()}
    return daten


def test_karten_tragen_filterwerte_als_data_attribute(startseite: str):
    daten = _karten_daten(startseite)
    assert len(daten) == 31
    assert daten["exit-ticket"] == {
        "kategorie": {"D"},
        "richtung": {"sus-an-lehrkraft", "selbst"},
        "zeitpunkt": {"stundenende"},
        "form": {"analog", "digital"},
        "druckvorlage": {"ja"},
    }
    assert daten["blitzlicht"]["druckvorlage"] == {"nein"}
    assert daten["wimmelbild-zuordnen"]["druckvorlage"] == {"nein"}  # nur Platzhalter-Vorlage


def test_beispielkombination_trifft_die_erwarteten_methoden(startseite: str):
    daten = _karten_daten(startseite)
    treffer = {
        m
        for m, d in daten.items()
        if "stundenende" in d["zeitpunkt"] and "analog" in d["form"] and "ja" in d["druckvorlage"]
    }
    assert treffer == STUNDENENDE_ANALOG_MIT_VORLAGE


def _filterleiste(html: str) -> str:
    return re.search(r'<form class="filterleiste".*?</form>', html, re.S).group(0)


def test_filterleiste_hat_gruppen_aus_filter_yaml_mit_checkboxen(startseite: str):
    leiste = _filterleiste(startseite)
    legenden = re.findall(r"<legend[^>]*>([^<]+)</legend>", leiste)
    # Kategorie bekommt eigene Auswahl (Issue #15)
    assert legenden == ["Feedbackrichtung", "Zeitpunkt", "Form", "Druckvorlage"]
    boxen = re.findall(r'<input type="checkbox" name="([a-z]+)" value="([a-z-]+)"', leiste)
    assert ("zeitpunkt", "stundenende") in boxen
    assert ("druckvorlage", "ja") in boxen
    assert len(boxen) == 4 + 6 + 2 + 2
    peer = re.search(r'<label[^>]*>\s*<input [^>]*value="peer"[^>]*>(.*?)</label>', leiste, re.S)
    assert re.sub(r"<[^>]+>", "", peer.group(1)).strip() == "SuS ↔ SuS"


def test_filterleiste_hat_zuruecksetzen_und_ist_ohne_js_ausgeblendet(startseite: str):
    leiste = _filterleiste(startseite)
    assert re.search(r'<button [^>]*type="reset"[^>]*>Filter zurücksetzen</button>', leiste)
    css = stylesheet("site")
    assert re.search(r"html:not\(\[data-js\]\) \.filterleiste\s*\{\s*display:\s*none", css)
    assert re.search(r"\.karte\[hidden\]\s*\{\s*display:\s*none", css)


def test_trefferzahl_ist_live_region_und_script_eingebunden(startseite: str):
    assert re.search(r'<p [^>]*class="uebersicht__anzahl"[^>]*aria-live="polite"', startseite)
    assert '<script src="/static/js/filter.js" defer></script>' in startseite


# --- Verhalten von filter.js (mit Node und einem Mini-DOM) --------------------------------

NODE = shutil.which("node")
braucht_node = pytest.mark.skipif(NODE is None, reason="Node.js nicht installiert")

# Baut aus den Karten-Daten ein Mini-DOM (Formular mit Checkboxen, Karten, Trefferzahl), lädt
# filter.js, setzt die gewünschten Haken, löst "change" (bzw. "reset") aus und meldet den Zustand.
STUB = r"""
const fs = require("fs");
const eingabe = JSON.parse(fs.readFileSync(0, "utf8"));
function element(attrs) {
  const a = Object.assign({}, attrs);
  const listener = {};
  return {
    hidden: false, textContent: "", checked: false,
    getAttribute: (k) => (k in a ? a[k] : null),
    hasAttribute: (k) => k in a,
    addEventListener: (t, f) => { (listener[t] = listener[t] || []).push(f); },
    feuern: (t, e) => (listener[t] || []).forEach((f) => f(e || { preventDefault() {} })),
  };
}
const boxen = eingabe.boxen.map(([name, value]) => Object.assign(
  element({ type: "checkbox" }), { name, value, type: "checkbox" }));
const formular = element({ "data-filterleiste": "" });
formular.querySelectorAll = () => boxen;
formular.reset = () => boxen.forEach((b) => { b.checked = false; });
const karten = Object.entries(eingabe.karten).map(([id, werte]) => {
  const attrs = { "data-methode": id };
  for (const [feld, w] of Object.entries(werte)) attrs["data-filter-" + feld] = w.join(" ");
  return element(attrs);
});
const zahl = element({ "data-trefferzahl": "" });
zahl.textContent = karten.length + " Methoden";
const leer = element({ "data-keine-treffer": "" });
leer.hidden = true;
const document = {
  querySelector: (s) => ({ "[data-filterleiste]": formular, "[data-trefferzahl]": zahl,
    "[data-keine-treffer]": leer })[s] || null,
  querySelectorAll: (s) => (s === "[data-methode]" ? karten : []),
};
const window = { setTimeout: (f) => f() };
const quelle = fs.readFileSync(eingabe.skript, "utf8");
new Function("document", "window", "setTimeout", "module", quelle)(
  document, window, window.setTimeout, undefined);
const zustand = () => ({
  sichtbar: karten.filter((k) => !k.hidden).map((k) => k.getAttribute("data-methode")),
  trefferzahl: zahl.textContent,
  leerSichtbar: !leer.hidden,
});
const ergebnis = {};
for (const box of boxen) {
  box.checked = eingabe.haken.some(([n, v]) => n === box.name && v === box.value);
}
formular.feuern("change");
ergebnis.gefiltert = zustand();
formular.reset();
formular.feuern("reset");
ergebnis.zurueckgesetzt = zustand();
process.stdout.write(JSON.stringify(ergebnis));
"""


def _laufen(startseite: str, haken: list[tuple[str, str]]) -> dict:
    daten = _karten_daten(startseite)
    boxen = re.findall(r'<input type="checkbox" name="([a-z]+)" value="([a-z-]+)"', startseite)
    eingabe = {
        "skript": str(Path("static/js/filter.js").resolve()),
        "karten": {m: {f: sorted(w) for f, w in d.items()} for m, d in daten.items()},
        "boxen": boxen,
        "haken": haken,
    }
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
def test_js_filtert_stundenende_analog_mit_vorlage(startseite: str):
    e = _laufen(
        startseite, [("zeitpunkt", "stundenende"), ("form", "analog"), ("druckvorlage", "ja")]
    )
    assert set(e["gefiltert"]["sichtbar"]) == STUNDENENDE_ANALOG_MIT_VORLAGE
    assert e["gefiltert"]["trefferzahl"] == "9 von 31 Methoden"
    assert e["gefiltert"]["leerSichtbar"] is False


@braucht_node
def test_js_oder_innerhalb_einer_gruppe(startseite: str):
    nur_einstieg = _laufen(startseite, [("zeitpunkt", "einstieg")])["gefiltert"]["sichtbar"]
    beide = _laufen(startseite, [("zeitpunkt", "einstieg"), ("zeitpunkt", "stundenende")])
    assert set(nur_einstieg) < set(beide["gefiltert"]["sichtbar"])
    assert "exit-ticket" in beide["gefiltert"]["sichtbar"]


@braucht_node
def test_js_zuruecksetzen_zeigt_alle_31(startseite: str):
    e = _laufen(startseite, [("form", "digital")])
    assert len(e["zurueckgesetzt"]["sichtbar"]) == 31
    assert e["zurueckgesetzt"]["trefferzahl"] == "31 Methoden"


@braucht_node
def test_js_meldet_wenn_nichts_passt(startseite: str):
    # Derzeit gibt es keine dauerhafte Peer-Feedback-Methode
    e = _laufen(startseite, [("zeitpunkt", "dauerhaft"), ("richtung", "peer")])
    if e["gefiltert"]["sichtbar"]:
        pytest.skip("Kombination hat inzwischen Treffer")
    assert e["gefiltert"]["trefferzahl"] == "0 von 31 Methoden"
    assert e["gefiltert"]["leerSichtbar"] is True
