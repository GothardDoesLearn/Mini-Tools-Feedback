"""Kategorie-Auswahl als Filter (Issue #15): Mehrfachauswahl, „Alle“, aria-pressed."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from generator.build import build

NODE = shutil.which("node")
BOX = r'<input type="checkbox" name="([a-z]+)" value="([a-z-]+)"'
braucht_node = pytest.mark.skipif(NODE is None, reason="Node.js nicht installiert")


@pytest.fixture(scope="module")
def startseite(tmp_path_factory) -> str:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return (out / "index.html").read_text(encoding="utf-8")


def _karten(html: str) -> dict[str, dict[str, list[str]]]:
    daten = {}
    for tag in re.findall(r'<article class="karte"[^>]*>', html):
        attrs = dict(re.findall(r'data-filter-([a-z]+)="([^"]*)"', tag))
        methoden_id = re.search(r'data-methode="([^"]+)"', tag).group(1)
        daten[methoden_id] = {feld: werte.split() for feld, werte in attrs.items()}
    return daten


def _kategorie_knoepfe(html: str) -> list[tuple[str, str]]:
    """(data-kategorie, aria-pressed) je Kategorie-Button, in Reihenfolge."""
    return re.findall(r'<button [^>]*data-kategorie="([^"]*)" aria-pressed="(true|false)"', html)


def test_alle_ist_im_html_vorausgewaehlt(startseite: str):
    knoepfe = _kategorie_knoepfe(startseite)
    assert knoepfe[0] == ("", "true")
    assert all(gedrueckt == "false" for _, gedrueckt in knoepfe[1:])
    assert len(knoepfe) > 2


# Mini-DOM: Formular mit Checkboxen, Kategorie-Buttons, Karten. Führt eine Folge von Schritten
# aus ({"klick": id} | {"haken": [name, value]} | {"reset": true}) und meldet nach jedem Schritt
# sichtbare Karten, Trefferzahl und die gedrückten Kategorie-Buttons.
STUB = r"""
const fs = require("fs");
const eingabe = JSON.parse(fs.readFileSync(0, "utf8"));
function element(attrs) {
  const a = Object.assign({}, attrs);
  const listener = {};
  return {
    hidden: false, textContent: "", checked: false,
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
const karten = Object.entries(eingabe.karten).map(([id, werte]) => {
  const attrs = { "data-methode": id };
  for (const [feld, w] of Object.entries(werte)) attrs["data-filter-" + feld] = w.join(" ");
  return element(attrs);
});
const zahl = element({ "data-trefferzahl": "" });
const leer = element({ "data-keine-treffer": "" });
const document = {
  querySelector: (s) => ({ "[data-filterleiste]": formular, "[data-trefferzahl]": zahl,
    "[data-keine-treffer]": leer })[s] || null,
  querySelectorAll: (s) => ({ "[data-methode]": karten, "[data-kategorie]": knoepfe })[s] || [],
};
const window = { setTimeout: (f) => f(), location: { assign() {} } };
const quelle = fs.readFileSync(eingabe.skript, "utf8");
new Function("document", "window", "setTimeout", "module", quelle)(
  document, window, window.setTimeout, undefined);
const ergebnisse = [];
for (const schritt of eingabe.schritte) {
  if ("klick" in schritt) {
    knoepfe.find((k) => k.getAttribute("data-kategorie") === schritt.klick).feuern("click");
  } else if ("haken" in schritt) {
    const [n, v] = schritt.haken;
    boxen.find((b) => b.name === n && b.value === v).checked = true;
    formular.feuern("change");
  } else if ("reset" in schritt) {
    boxen.forEach((b) => { b.checked = false; });
    formular.feuern("reset");
  }
  ergebnisse.push({
    sichtbar: karten.filter((k) => !k.hidden).map((k) => k.getAttribute("data-methode")),
    trefferzahl: zahl.textContent,
    gedrueckt: knoepfe.filter((k) => k.getAttribute("aria-pressed") === "true")
      .map((k) => k.getAttribute("data-kategorie")),
  });
}
process.stdout.write(JSON.stringify(ergebnisse));
"""


def _laufen(startseite: str, schritte: list[dict]) -> list[dict]:
    eingabe = {
        "skript": str(Path("static/js/filter.js").resolve()),
        "karten": _karten(startseite),
        "boxen": re.findall(BOX, startseite),
        "kategorien": [k for k, _ in _kategorie_knoepfe(startseite)],
        "schritte": schritte,
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


def _ids_der_kategorie(startseite: str, *kategorien: str) -> set[str]:
    return {m for m, d in _karten(startseite).items() if set(d["kategorie"]) & set(kategorien)}


@braucht_node
def test_eine_kategorie_zeigt_nur_ihre_karten(startseite: str):
    (e,) = _laufen(startseite, [{"klick": "D"}])
    erwartet = _ids_der_kategorie(startseite, "D")
    assert set(e["sichtbar"]) == erwartet
    assert "exit-ticket" in erwartet
    assert e["trefferzahl"] == f"{len(erwartet)} von 31 Methoden"
    assert e["gedrueckt"] == ["D"]


@braucht_node
def test_mehrere_kategorien_sind_oder_verknuepft(startseite: str):
    e = _laufen(startseite, [{"klick": "A"}, {"klick": "D"}])[-1]
    assert set(e["sichtbar"]) == _ids_der_kategorie(startseite, "A", "D")
    assert sorted(e["gedrueckt"]) == ["A", "D"]


@braucht_node
def test_erneuter_klick_hebt_kategorie_auf_und_alle_wird_wieder_gewaehlt(startseite: str):
    e = _laufen(startseite, [{"klick": "D"}, {"klick": "D"}])[-1]
    assert len(e["sichtbar"]) == 31
    assert e["gedrueckt"] == [""]
    assert e["trefferzahl"] == "31 Methoden"


@braucht_node
def test_alle_hebt_die_auswahl_auf(startseite: str):
    e = _laufen(startseite, [{"klick": "A"}, {"klick": "D"}, {"klick": ""}])[-1]
    assert len(e["sichtbar"]) == 31
    assert e["gedrueckt"] == [""]


@braucht_node
def test_kategorie_und_filtergruppen_sind_und_verknuepft(startseite: str):
    e = _laufen(startseite, [{"klick": "D"}, {"haken": ["form", "digital"]}])[-1]
    daten = _karten(startseite)
    erwartet = {m for m, d in daten.items() if "D" in d["kategorie"] and "digital" in d["form"]}
    assert set(e["sichtbar"]) == erwartet
    assert erwartet < _ids_der_kategorie(startseite, "D")


@braucht_node
def test_zuruecksetzen_leert_auch_die_kategorien(startseite: str):
    e = _laufen(startseite, [{"klick": "D"}, {"reset": True}])[-1]
    assert len(e["sichtbar"]) == 31
    assert e["gedrueckt"] == [""]
