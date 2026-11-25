"""Ansichts-Umschalter (Issue #6): Knopfgruppe im Kopf, Wahl in localStorage, kein Flackern."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from generator.build import build


@pytest.fixture(scope="module")
def dist(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return out


@pytest.fixture(scope="module")
def startseite(dist: Path) -> str:
    return (dist / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def css(dist: Path) -> str:
    text = (dist / "static" / "css" / "site.css").read_text(encoding="utf-8")
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def _gruppe(html: str) -> str:
    return re.search(r'<div [^>]*role="group"[^>]*>.*?</div>', html, re.S).group(0)


def _kopf_script(html: str) -> str:
    head = re.search(r"<head>(.*?)</head>", html, re.S).group(1)
    return re.search(r"<script>(.*?)</script>", head, re.S).group(1)


def test_umschalter_ist_gruppe_aus_zwei_knoepfen_im_kopf(startseite: str):
    kopf = re.search(r'<header class="kopf">.*?</header>', startseite, re.S).group(0)
    gruppe = _gruppe(kopf)
    assert 'aria-label="Ansicht wählen"' in gruppe
    knoepfe = re.findall(r"<button ([^>]*)>\s*([^<]+?)\s*</button>", gruppe)
    assert [label for _, label in knoepfe] == ["Pinnwand", "Klare Ansicht"]
    for attrs, _ in knoepfe:
        assert 'type="button"' in attrs


def test_ohne_gespeicherte_wahl_ist_pinnwand_voreingestellt(startseite: str):
    assert '<html lang="de" data-ansicht="pinnwand">' in startseite
    pressed = dict(
        (label, wert)
        for wert, label in re.findall(
            r'<button [^>]*aria-pressed="(true|false)"[^>]*>\s*([^<]+?)\s*</button>',
            _gruppe(startseite),
        )
    )
    assert pressed == {"Pinnwand": "true", "Klare Ansicht": "false"}


def test_inline_script_steht_im_head_vor_dem_stylesheet(startseite: str):
    head = re.search(r"<head>(.*?)</head>", startseite, re.S).group(1)
    assert head.index("<script>") < head.index('<link rel="stylesheet"')
    assert "mt-ansicht" in _kopf_script(startseite)


def test_umschalter_ist_ohne_javascript_ausgeblendet(css: str):
    assert re.search(r"html:not\(\[data-js\]\) \.ansichtswahl\s*\{\s*display:\s*none", css)


def test_gewaehlter_knopf_wird_ueber_das_html_attribut_hervorgehoben(css: str):
    # Hervorhebung hängt am <html>-Attribut, das das Inline-Script vor dem ersten Rendern setzt.
    assert '[data-ansicht="klar"] .ansichtswahl__knopf[data-ansicht-wahl="klar"]' in css
    assert '[data-ansicht="pinnwand"] .ansichtswahl__knopf[data-ansicht-wahl="pinnwand"]' in css


def test_umschalter_ist_im_druck_ausgeblendet(css: str):
    selektoren = re.search(r"@media print\s*\{([^{]*)\{\s*display:\s*none", css).group(1)
    assert ".kopf" in selektoren or ".ansichtswahl" in selektoren


# --- Verhalten des Inline-Scripts (mit Node und einem Mini-DOM) ---------------------------

NODE = shutil.which("node")

STUB = r"""
const fs = require("fs");
const [skript, szenario] = [fs.readFileSync(0, "utf8"), JSON.parse(process.argv[1])];
const attrs = { "data-ansicht": "pinnwand" };
const html = {
  setAttribute: (k, v) => { attrs[k] = String(v); },
  getAttribute: (k) => (k in attrs ? attrs[k] : null),
};
function knopf(wert) {
  const a = { "data-ansicht-wahl": wert, "aria-pressed": wert === "pinnwand" ? "true" : "false" };
  return {
    setAttribute: (k, v) => { a[k] = String(v); },
    getAttribute: (k) => (k in a ? a[k] : null),
    closest() { return this; },
  };
}
const knoepfe = [knopf("pinnwand"), knopf("klar")];
const listener = {};
const fensterListener = {};
let speicher = szenario.gespeichert === undefined ? {} : { "mt-ansicht": szenario.gespeichert };
const localStorage = szenario.speicherKaputt
  ? { getItem() { throw new Error("x"); }, setItem() { throw new Error("x"); } }
  : {
      getItem: (k) => (k in speicher ? speicher[k] : null),
      setItem: (k, v) => { speicher[k] = v; },
    };
const document = {
  documentElement: html,
  querySelectorAll: () => knoepfe,
  addEventListener: (t, f) => { (listener[t] = listener[t] || []).push(f); },
};
const window = {
  addEventListener: (t, f) => { (fensterListener[t] = fensterListener[t] || []).push(f); },
};
new Function("document", "window", "localStorage", skript)(document, window, localStorage);
const zustand = () => ({
  ansicht: attrs["data-ansicht"],
  js: "data-js" in attrs,
  pressed: knoepfe.map((k) => k.getAttribute("aria-pressed")),
  gespeichert: speicher["mt-ansicht"] ?? null,
});
const ergebnis = { start: zustand() };
(listener.DOMContentLoaded || []).forEach((f) => f());
ergebnis.geladen = zustand();
if (szenario.klick) {
  const ziel = knoepfe.find((k) => k.getAttribute("data-ansicht-wahl") === szenario.klick);
  (listener.click || []).forEach((f) => f({ target: ziel }));
  ergebnis.geklickt = zustand();
}
if (szenario.andererTab) {
  const ereignis = { key: "mt-ansicht", newValue: szenario.andererTab };
  (fensterListener.storage || []).forEach((f) => f(ereignis));
  ergebnis.andererTab = zustand();
}
process.stdout.write(JSON.stringify(ergebnis));
"""


def _laufen(skript: str, **szenario) -> dict:
    r = subprocess.run(
        [NODE, "-e", STUB, json.dumps(szenario)],
        input=skript,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(r.stdout)


braucht_node = pytest.mark.skipif(NODE is None, reason="Node.js nicht installiert")


@braucht_node
def test_script_ohne_gespeicherte_wahl_bleibt_pinnwand(startseite: str):
    e = _laufen(_kopf_script(startseite))
    assert e["start"]["ansicht"] == "pinnwand"
    assert e["start"]["js"] is True
    assert e["geladen"]["pressed"] == ["true", "false"]


@braucht_node
def test_script_setzt_gespeicherte_wahl_sofort_im_head(startseite: str):
    e = _laufen(_kopf_script(startseite), gespeichert="klar")
    assert e["start"]["ansicht"] == "klar"  # vor dem ersten Rendern -> kein Flackern
    assert e["geladen"]["pressed"] == ["false", "true"]


@braucht_node
def test_script_ignoriert_ungueltige_gespeicherte_werte(startseite: str):
    e = _laufen(_kopf_script(startseite), gespeichert="<script>")
    assert e["geladen"]["ansicht"] == "pinnwand"


@braucht_node
def test_klick_schaltet_um_und_speichert_wahl(startseite: str):
    e = _laufen(_kopf_script(startseite), klick="klar")
    assert e["geklickt"] == {
        "ansicht": "klar",
        "js": True,
        "pressed": ["false", "true"],
        "gespeichert": "klar",
    }


@braucht_node
def test_blockierter_speicher_bricht_nichts(startseite: str):
    e = _laufen(_kopf_script(startseite), speicherKaputt=True, klick="klar")
    assert e["start"]["ansicht"] == "pinnwand"
    assert e["geklickt"]["ansicht"] == "klar"


@braucht_node
def test_wahl_in_anderem_tab_wirkt_sofort(startseite: str):
    e = _laufen(_kopf_script(startseite), andererTab="klar")
    assert e["andererTab"]["ansicht"] == "klar"
    assert e["andererTab"]["pressed"] == ["false", "true"]
