"""Filterzustand in der URL (Issue #16): Query-Parameter <-> Kategorie- und Filterauswahl."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from generator.build import build

NODE = shutil.which("node")
BOX = r'<input type="checkbox" name="([a-z]+)" value="([a-z-]+)"'
pytestmark = pytest.mark.skipif(NODE is None, reason="Node.js nicht installiert")


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


def _kategorien(html: str) -> list[str]:
    return re.findall(r'<button [^>]*data-kategorie="([^"]*)"', html)


# Mini-DOM mit window.location/history. Startet mit eingabe.search, führt Schritte aus
# ({"klick": id} | {"haken": [name, value]} | {"reset": true} | {"zurueck": search}) und meldet
# nach jedem Schritt sichtbare Karten, gedrückte Kategorien, angehakte Boxen und die URL.
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
const document = {
  querySelector: (s) => (s === "[data-filterleiste]" ? formular : null),
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
const quelle = fs.readFileSync(eingabe.skript, "utf8");
function zustand() {
  return {
    sichtbar: karten.filter((k) => !k.hidden).map((k) => k.getAttribute("data-methode")),
    gedrueckt: knoepfe.filter((k) => k.getAttribute("aria-pressed") === "true")
      .map((k) => k.getAttribute("data-kategorie")),
    angehakt: boxen.filter((b) => b.checked).map((b) => b.name + "=" + b.value),
    search: location.search,
    verlauf: verlauf.splice(0),
  };
}
new Function("document", "window", "setTimeout", "module", quelle)(
  document, window, window.setTimeout, undefined);
const ergebnisse = [zustand()];
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
  } else if ("zurueck" in schritt) {
    location.search = schritt.zurueck;
    (fensterListener.popstate || []).forEach((f) => f({}));
  }
  ergebnisse.push(zustand());
}
process.stdout.write(JSON.stringify(ergebnisse));
"""


def _laufen(startseite: str, search: str = "", schritte: list[dict] | None = None) -> list[dict]:
    eingabe = {
        "skript": str(Path("static/js/filter.js").resolve()),
        "karten": _karten(startseite),
        "boxen": re.findall(BOX, startseite),
        "kategorien": _kategorien(startseite),
        "search": search,
        "schritte": schritte or [],
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


def _erwartet(startseite: str, kategorien: set[str], form: str | None = None) -> set[str]:
    return {
        m
        for m, d in _karten(startseite).items()
        if set(d["kategorie"]) & kategorien and (form is None or form in d["form"])
    }


def test_link_mit_filtern_oeffnet_die_gefilterte_ansicht(startseite: str):
    (e,) = _laufen(startseite, "?kategorie=A,D&form=digital")
    assert sorted(e["gedrueckt"]) == ["A", "D"]
    assert e["angehakt"] == ["form=digital"]
    assert set(e["sichtbar"]) == _erwartet(startseite, {"A", "D"}, "digital")
    assert e["verlauf"] == []  # gültige URL bleibt unverändert


def test_ohne_parameter_bleibt_alles_sichtbar_und_url_unveraendert(startseite: str):
    (e,) = _laufen(startseite, "")
    assert len(e["sichtbar"]) == 31
    assert e["gedrueckt"] == [""]
    assert e["verlauf"] == []


def test_bedienung_schreibt_die_url_als_neuen_verlaufseintrag(startseite: str):
    _, nach_klick, nach_haken = _laufen(
        startseite, "", [{"klick": "D"}, {"haken": ["form", "digital"]}]
    )
    assert nach_klick["verlauf"] == [["push", "/?kategorie=D"]]
    assert nach_haken["verlauf"] == [["push", "/?kategorie=D&form=digital"]]


def test_zuruecksetzen_entfernt_die_parameter(startseite: str):
    e = _laufen(startseite, "?kategorie=D&form=digital", [{"reset": True}])[-1]
    assert e["verlauf"] == [["push", "/"]]
    assert len(e["sichtbar"]) == 31


def test_unveraenderter_zustand_erzeugt_keinen_verlaufseintrag(startseite: str):
    e = _laufen(startseite, "", [{"klick": ""}])[-1]
    assert e["verlauf"] == []


def test_ungueltige_parameter_werden_ignoriert(startseite: str):
    (e,) = _laufen(startseite, "?kategorie=Z,D,%3Cx%3E&form=quatsch&zeitpunkt=&richtung")
    assert e["gedrueckt"] == ["D"]
    assert e["angehakt"] == []
    assert set(e["sichtbar"]) == _erwartet(startseite, {"D"})
    # URL wird still bereinigt (kein neuer Verlaufseintrag)
    assert e["verlauf"] == [["replace", "/?kategorie=D"]]


def test_fremde_parameter_bleiben_erhalten(startseite: str):
    e = _laufen(startseite, "?utm=x", [{"klick": "D"}])[-1]
    assert e["verlauf"] == [["push", "/?kategorie=D&utm=x"]]


def test_zurueck_im_browser_stellt_den_vorherigen_zustand_her(startseite: str):
    e = _laufen(
        startseite,
        "",
        [{"klick": "D"}, {"haken": ["form", "digital"]}, {"zurueck": "?kategorie=D"}],
    )[-1]
    assert e["gedrueckt"] == ["D"]
    assert e["angehakt"] == []
    assert set(e["sichtbar"]) == _erwartet(startseite, {"D"})
    assert e["verlauf"] == []  # Zurück erzeugt selbst keinen Eintrag


def test_vor_bis_zum_anfang_hebt_alle_filter_auf(startseite: str):
    e = _laufen(startseite, "?kategorie=D", [{"zurueck": ""}])[-1]
    assert e["gedrueckt"] == [""]
    assert len(e["sichtbar"]) == 31


def test_erzeugte_url_in_neuem_tab_ergibt_dieselbe_ansicht(startseite: str):
    schritte = [{"klick": "B"}, {"klick": "E"}, {"haken": ["zeitpunkt", "stundenende"]}]
    *_, vorher = _laufen(startseite, "", schritte)
    (neu,) = _laufen(startseite, vorher["search"])
    assert neu["sichtbar"] == vorher["sichtbar"]
    assert neu["gedrueckt"] == vorher["gedrueckt"]
    assert neu["angehakt"] == vorher["angehakt"]
