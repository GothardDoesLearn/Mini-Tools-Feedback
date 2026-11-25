"""Dauer-Filter (Issue #19): Schieberegler „max. Minuten“ nutzt dauer_min/dauer_max.

Eine Methode passt, wenn ihre längste Dauer (`dauer_max`) in die gewählten Minuten passt.
Methoden mit `dauerhaft` (0/0) erscheinen immer.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from generator.build import build

NODE = shutil.which("node")
BOX = r'<input type="checkbox" name="([a-z]+)" value="([a-z-]+)"'

# Von Hand aus content/methoden ermittelt (dauer_max <= 2, dazu die beiden „dauerhaft“).
BIS_2_MINUTEN = {
    "ampel",
    "daumenprobe",
    "namen-ziehen",
    "smileys",
    "fahrstuhlmethode",
    "wetterbericht",
    "briefkasten",
    "laermampel",
}


@pytest.fixture(scope="module")
def startseite(tmp_path_factory) -> str:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return (out / "index.html").read_text(encoding="utf-8")


def _karten(html: str) -> dict[str, dict]:
    daten = {}
    for tag in re.findall(r'<article class="karte"[^>]*>', html):
        methoden_id = re.search(r'data-methode="([^"]+)"', tag).group(1)
        filter_attrs = dict(re.findall(r'data-filter-([a-z]+)="([^"]*)"', tag))
        dauer = dict(re.findall(r'data-dauer-(min|max)="([^"]*)"', tag))
        daten[methoden_id] = {
            "werte": {feld: w.split() for feld, w in filter_attrs.items()},
            "dauer": dauer,
        }
    return daten


def _regler(html: str) -> dict[str, str]:
    tag = re.search(r"<input [^>]*data-dauer-regler[^>]*>", html)
    assert tag, "Schieberegler fehlt"
    return dict(re.findall(r'([a-z-]+)="([^"]*)"', tag.group(0)))


def test_karten_tragen_dauer_min_und_max(startseite: str):
    karten = _karten(startseite)
    assert karten["mini-whiteboards"]["dauer"] == {"min": "1", "max": "3"}
    assert karten["laermampel"]["dauer"] == {"min": "0", "max": "0"}
    assert all(set(k["dauer"]) == {"min", "max"} for k in karten.values())


def test_regler_ist_beschriftet_und_reicht_bis_zur_laengsten_methode(startseite: str):
    regler = _regler(startseite)
    assert regler["type"] == "range"
    assert (regler["min"], regler["max"], regler["step"]) == ("1", "15", "1")
    assert regler["value"] == "15"  # Grundzustand: keine Einschränkung
    label = re.search(rf'<label [^>]*for="{regler["id"]}"[^>]*>([^<]+)</label>', startseite)
    assert label and "Dauer" in label.group(1)
    # Anzeige des gewählten Werts, mit dem Regler verknüpft
    assert re.search(rf'<output [^>]*for="{regler["id"]}"', startseite)


def test_regler_steht_in_der_filterleiste(startseite: str):
    formular = re.search(r"<form [^>]*data-filterleiste.*?</form>", startseite, re.S).group(0)
    assert "data-dauer-regler" in formular


# Mini-DOM wie tests/test_filter_url.py, zusätzlich Regler und <output>. Schritte:
# {"dauer": n} (Regler auf n, input + change) | {"haken": [name, value]} | {"reset": true}
STUB = r"""
const fs = require("fs");
const eingabe = JSON.parse(fs.readFileSync(0, "utf8"));
function element(attrs) {
  const a = Object.assign({}, attrs);
  const listener = {};
  return {
    hidden: false, textContent: "", checked: false, disabled: false,
    getAttribute: (k) => (k in a ? a[k] : null),
    setAttribute: (k, v) => { a[k] = String(v); },
    hasAttribute: (k) => k in a,
    addEventListener: (t, f) => { (listener[t] = listener[t] || []).push(f); },
    feuern: (t, e) => (listener[t] || []).forEach((f) => f(e || { preventDefault() {} })),
  };
}
const boxen = eingabe.boxen.map(([name, value]) => Object.assign(
  element({ type: "checkbox" }), { name, value, type: "checkbox" }));
const r = eingabe.regler;
const regler = Object.assign(element(r), {
  type: "range", min: r.min, max: r.max, value: r.value, defaultValue: r.value });
const anzeige = element({ "data-dauer-anzeige": "" });
const formular = element({ "data-filterleiste": "" });
formular.querySelectorAll = () => boxen;
const karten = Object.entries(eingabe.karten).map(([id, k]) => {
  const attrs = { "data-methode": id };
  for (const [feld, w] of Object.entries(k.werte)) attrs["data-filter-" + feld] = w.join(" ");
  attrs["data-dauer-min"] = k.dauer.min;
  attrs["data-dauer-max"] = k.dauer.max;
  return element(attrs);
});
const trefferzahl = element({});
const document = {
  querySelector: (s) => ({ "[data-filterleiste]": formular, "[data-dauer-regler]": regler,
    "[data-dauer-anzeige]": anzeige, "[data-trefferzahl]": trefferzahl })[s] || null,
  querySelectorAll: (s) => ({ "[data-methode]": karten })[s] || [],
};
const verlauf = [];
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
  addEventListener: () => {},
};
function zustand() {
  return {
    sichtbar: karten.filter((k) => !k.hidden).map((k) => k.getAttribute("data-methode")),
    regler: regler.value,
    anzeige: anzeige.textContent,
    valuetext: regler.getAttribute("aria-valuetext"),
    treffer: trefferzahl.textContent,
    search: location.search,
    verlauf: verlauf.splice(0),
  };
}
new Function("document", "window", "setTimeout", "module", fs.readFileSync(eingabe.skript, "utf8"))(
  document, window, window.setTimeout, undefined);
const ergebnisse = [zustand()];
for (const schritt of eingabe.schritte) {
  if ("dauer" in schritt) {
    regler.value = String(schritt.dauer);
    regler.feuern("input");
    formular.feuern("change");
  } else if ("haken" in schritt) {
    const [n, v] = schritt.haken;
    boxen.find((b) => b.name === n && b.value === v).checked = true;
    formular.feuern("change");
  } else if ("reset" in schritt) {
    boxen.forEach((b) => { b.checked = false; });
    regler.value = regler.defaultValue;
    formular.feuern("reset");
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
        "regler": _regler(startseite),
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


js = pytest.mark.skipif(NODE is None, reason="Node.js nicht installiert")


@js
def test_grundzustand_zeigt_alle_methoden(startseite: str):
    (e,) = _laufen(startseite)
    assert len(e["sichtbar"]) == 31
    assert e["anzeige"] == "beliebig"
    assert e["verlauf"] == []


@js
def test_bis_2_minuten_filtert_korrekt(startseite: str):
    e = _laufen(startseite, "", [{"dauer": 2}])[-1]
    assert set(e["sichtbar"]) == BIS_2_MINUTEN
    assert e["anzeige"] == "bis 2 Min"
    assert e["valuetext"] == "bis 2 Minuten"
    assert e["treffer"] == "8 von 31 Methoden"


@js
def test_dauerhafte_methoden_erscheinen_bei_jedem_reglerwert(startseite: str):
    e = _laufen(startseite, "", [{"dauer": 1}])[-1]
    assert {"briefkasten", "laermampel"} <= set(e["sichtbar"])


@js
def test_dauer_kombiniert_mit_anderen_filtern(startseite: str):
    e = _laufen(startseite, "", [{"dauer": 2}, {"haken": ["zeitpunkt", "stundenende"]}])[-1]
    assert set(e["sichtbar"]) == {"smileys", "wetterbericht"}


@js
def test_dauer_steht_in_der_url(startseite: str):
    e = _laufen(startseite, "", [{"dauer": 2}])[-1]
    assert e["verlauf"] == [["push", "/?dauer=2"]]


@js
def test_link_mit_dauer_stellt_den_regler_ein(startseite: str):
    (e,) = _laufen(startseite, "?dauer=2")
    assert e["regler"] == "2"
    assert set(e["sichtbar"]) == BIS_2_MINUTEN
    assert e["verlauf"] == []


@js
@pytest.mark.parametrize("wert", ["abc", "0", "99", "2.5", "-3"])
def test_ungueltige_dauer_in_der_url_wird_ignoriert(startseite: str, wert: str):
    (e,) = _laufen(startseite, f"?dauer={wert}")
    assert e["regler"] == "15"
    assert len(e["sichtbar"]) == 31
    assert e["verlauf"] == [["replace", "/"]]


@js
def test_regler_auf_maximum_entfernt_den_parameter(startseite: str):
    e = _laufen(startseite, "?dauer=2", [{"dauer": 15}])[-1]
    assert e["verlauf"] == [["push", "/"]]
    assert e["anzeige"] == "beliebig"


@js
def test_zuruecksetzen_stellt_den_regler_zurueck(startseite: str):
    e = _laufen(startseite, "?dauer=2", [{"reset": True}])[-1]
    assert len(e["sichtbar"]) == 31
    assert e["anzeige"] == "beliebig"
    assert e["verlauf"] == [["push", "/"]]
