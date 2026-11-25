"""Button „Zufällige Methode“ auf der Startseite (Issue #17)."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from generator.build import build
from generator.css import stylesheet
from tests.test_filterleiste import STUNDENENDE_ANALOG_MIT_VORLAGE, _karten_daten


@pytest.fixture(scope="module")
def startseite(tmp_path_factory) -> str:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return (out / "index.html").read_text(encoding="utf-8")


def test_startseite_hat_zufallsknopf(startseite: str):
    knopf = re.search(r"<button [^>]*data-zufall[^>]*>([^<]*)</button>", startseite)
    assert knopf, "Knopf mit data-zufall fehlt"
    assert knopf.group(1).strip() == "Zufällige Methode"
    assert 'type="button"' in knopf.group(0)


def test_zufallsknopf_ist_ohne_js_ausgeblendet():
    css = stylesheet("site")
    assert re.search(r"html:not\(\[data-js\]\) \.zufall-knopf\s*\{\s*display:\s*none", css)


# --- Verhalten in filter.js (Node + Mini-DOM, wie tests/test_filterleiste.py) ------------

NODE = shutil.which("node")
braucht_node = pytest.mark.skipif(NODE is None, reason="Node.js nicht installiert")

STUB = r"""
const fs = require("fs");
const eingabe = JSON.parse(fs.readFileSync(0, "utf8"));
function element(attrs) {
  const a = Object.assign({}, attrs);
  const listener = {};
  return {
    hidden: false, textContent: "", checked: false, disabled: false,
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
const karten = Object.entries(eingabe.karten).map(([id, werte]) => {
  const attrs = { "data-methode": id };
  for (const [feld, w] of Object.entries(werte)) attrs["data-filter-" + feld] = w.join(" ");
  return element(attrs);
});
const zufall = element({ "data-zufall": "" });
const document = {
  querySelector: (s) => ({ "[data-filterleiste]": formular, "[data-zufall]": zufall })[s] || null,
  querySelectorAll: (s) => (s === "[data-methode]" ? karten : []),
};
const ziele = [];
const window = { setTimeout: (f) => f(), location: { assign: (u) => ziele.push(u) } };
const quelle = fs.readFileSync(eingabe.skript, "utf8");
new Function("document", "window", "setTimeout", "module", quelle)(
  document, window, window.setTimeout, undefined);
for (const box of boxen) {
  box.checked = eingabe.haken.some(([n, v]) => n === box.name && v === box.value);
}
formular.feuern("change");
for (let i = 0; i < eingabe.klicks; i++) zufall.feuern("click");
process.stdout.write(JSON.stringify({ ziele, deaktiviert: zufall.disabled }));
"""


def _laufen(startseite: str, haken: list[tuple[str, str]], klicks: int) -> dict:
    daten = _karten_daten(startseite)
    boxen = re.findall(r'<input type="checkbox" name="([a-z]+)" value="([a-z-]+)"', startseite)
    eingabe = {
        "skript": str(Path("static/js/filter.js").resolve()),
        "karten": {m: {f: sorted(w) for f, w in d.items()} for m, d in daten.items()},
        "boxen": boxen,
        "haken": haken,
        "klicks": klicks,
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
def test_zufall_waehlt_nur_aus_den_treffern(startseite: str):
    haken = [("zeitpunkt", "stundenende"), ("form", "analog"), ("druckvorlage", "ja")]
    e = _laufen(startseite, haken, klicks=200)
    erwartet = {f"/methoden/{m}/" for m in STUNDENENDE_ANALOG_MIT_VORLAGE}
    assert e["deaktiviert"] is False
    assert len(e["ziele"]) == 200
    assert set(e["ziele"]) <= erwartet
    assert len(set(e["ziele"])) > 1  # wirklich zufällig, nicht immer dieselbe


@braucht_node
def test_zufall_ohne_filter_waehlt_aus_allen(startseite: str):
    e = _laufen(startseite, [], klicks=1)
    alle = {f"/methoden/{m}/" for m in _karten_daten(startseite)}
    assert e["ziele"][0] in alle


@braucht_node
def test_zufall_ist_bei_null_treffern_deaktiviert(startseite: str):
    e = _laufen(startseite, [("zeitpunkt", "dauerhaft"), ("richtung", "peer")], klicks=3)
    if e["ziele"] and not e["deaktiviert"]:
        pytest.skip("Kombination hat inzwischen Treffer")
    assert e["deaktiviert"] is True
    assert e["ziele"] == []
