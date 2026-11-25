"""Ansicht „Pinnwand“ (Issue #5): Tokens, lokale Schriften, Handschrift ab 22 px, Kontrast,
reduzierte Bewegung und Druck in der klaren Ansicht."""

import re
from pathlib import Path

import pytest

from generator.build import build

PINNWAND = '[data-ansicht="pinnwand"]'
REDUZIERT = "screen and (prefers-reduced-motion: reduce)"


@pytest.fixture(scope="module")
def dist(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    build(output_dir=out)
    return out


@pytest.fixture(scope="module")
def css(dist: Path) -> str:
    text = (dist / "static" / "css" / "site.css").read_text(encoding="utf-8")
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def _bloecke(css: str, query: str) -> list[tuple[int, int]]:
    """Start/Ende aller @media-Blöcke mit genau dieser Query (inkl. Klammern)."""
    treffer = []
    for m in re.finditer(rf"@media {re.escape(query)}\s*\{{", css):
        tiefe = 0
        for i in range(m.end() - 1, len(css)):
            tiefe += {"{": 1, "}": -1}.get(css[i], 0)
            if tiefe == 0:
                treffer.append((m.start(), i + 1))
                break
    return treffer


def _media(css: str, query: str) -> str:
    return "".join(css[a:b] for a, b in _bloecke(css, query))


def _tokens(block: str) -> dict[str, str]:
    return dict(re.findall(r"(--[\w-]+):\s*([^;]+);", block))


def _token_block(css: str, selektor: str) -> str:
    return re.search(rf"{re.escape(selektor)}\s*\{{([^{{}}]*)\}}", css).group(1)


@pytest.fixture(scope="module")
def pinnwand_tokens(css: str) -> dict[str, str]:
    return _tokens(_token_block(_media(css, "screen"), PINNWAND))


@pytest.fixture(scope="module")
def klar_tokens(css: str) -> dict[str, str]:
    return _tokens(_token_block(css, '[data-ansicht="klar"]'))


def test_pinnwand_definiert_tokens_aus_design_md(pinnwand_tokens: dict[str, str]):
    erwartet = {
        "--farbe-hintergrund": "#8F8B8E",
        "--farbe-text": "#22262B",
        "--farbe-nebentext": "#3C434B",
        "--farbe-akzent": "#0E7C7B",
    }
    for name, wert in erwartet.items():
        assert pinnwand_tokens[name].upper() == wert, name


def test_pinnwand_nutzt_dieselben_token_namen_wie_klar(pinnwand_tokens, klar_tokens):
    assert set(klar_tokens) <= set(pinnwand_tokens)


def test_caveat_und_nunito_werden_lokal_als_woff2_geladen(dist: Path, css: str):
    faces = re.findall(r"@font-face\s*\{([^}]*)\}", css)
    gefunden = set()
    for face in faces:
        familie = re.search(r'font-family:\s*"([^"]+)"', face).group(1)
        gewicht = re.search(r"font-weight:\s*(\d+)", face).group(1)
        quelle = re.search(r'url\("?(/static/fonts/[^")]+\.woff2)"?\)', face).group(1)
        assert (dist / quelle.lstrip("/")).is_file(), quelle
        gefunden.add((familie, gewicht))
    assert ("Caveat", "700") in gefunden
    for gewicht in ("400", "600", "700"):
        assert ("Nunito", gewicht) in gefunden
    for familie in ("caveat", "nunito"):
        assert (dist / "static" / "fonts" / familie / "OFL.txt").is_file()


def test_pinnwand_schriften_kommen_ueber_tokens(pinnwand_tokens: dict[str, str]):
    assert pinnwand_tokens["--schrift-titel"].startswith('"Caveat"')
    assert pinnwand_tokens["--schrift-text"].startswith('"Nunito"')


def _px(wert: str) -> float:
    """Kleinster Wert einer font-size-Angabe in px (clamp/max: das Minimum)."""
    werte = [float(z) * (16 if e == "rem" else 1) for z, e in re.findall(r"([\d.]+)(px|rem)", wert)]
    assert werte, wert
    if wert.startswith("max("):
        return max(werte)
    if wert.startswith("clamp("):
        return werte[0]
    return min(werte)


def test_handschrift_nur_ab_22px(css: str):
    # Caveat nur über das Token, nirgends direkt als font-family.
    direkt = re.findall(r"font-family:\s*\"Caveat\"", css)
    assert len(direkt) == 1  # nur in @font-face

    screen = _media(css, "screen")
    for tag in ("h1", "h2", "h3"):
        regel = re.search(rf"{re.escape(PINNWAND)} {tag}\s*\{{([^}}]*)\}}", screen)
        assert regel, tag
        groesse = re.search(r"font-size:\s*([^;]+);", regel.group(1)).group(1)
        assert _px(groesse) >= 22, tag

    # Jede weitere Regel, die die Titelschrift nutzt, braucht selbst mindestens 22 px.
    for selektor, inhalt in re.findall(r"([^{}]+)\{([^{}]*var\(--schrift-titel\)[^{}]*)\}", css):
        if selektor.strip() == "h1,\nh2,\nh3":
            continue
        groesse = re.search(r"font-size:\s*([^;]+);", inhalt)
        assert groesse and _px(groesse.group(1)) >= 22, selektor.strip()


def _luminanz(hexwert: str) -> float:
    h = hexwert.strip().lstrip("#")
    kanaele = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in kanaele]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _kontrast(a: str, b: str) -> float:
    hell, dunkel = sorted((_luminanz(a), _luminanz(b)), reverse=True)
    return (hell + 0.05) / (dunkel + 0.05)


TEXT_PAARE = [
    ("--farbe-text", "--farbe-hintergrund"),
    ("--farbe-text", "--farbe-flaeche"),
    ("--farbe-nebentext", "--farbe-flaeche"),
    ("--farbe-akzent", "--farbe-flaeche"),
    ("--farbe-akzent-text", "--farbe-akzent"),
    ("--farbe-link", "--farbe-hintergrund"),
    ("--farbe-link", "--farbe-flaeche"),
]


@pytest.mark.parametrize("ansicht", ["klar", "pinnwand"])
def test_kontrast_wcag_aa(ansicht, klar_tokens, pinnwand_tokens):
    tokens = klar_tokens if ansicht == "klar" else pinnwand_tokens
    for vorne, hinten in TEXT_PAARE:
        assert _kontrast(tokens[vorne], tokens[hinten]) >= 4.5, (ansicht, vorne, hinten)
    # Fokusrahmen: Nicht-Text-Kontrast 3:1 auf Hintergrund und Fläche.
    for hinten in ("--farbe-hintergrund", "--farbe-flaeche"):
        assert _kontrast(tokens["--farbe-fokus"], tokens[hinten]) >= 3, (ansicht, hinten)


def test_druck_nutzt_immer_die_klare_ansicht(css: str):
    bloecke = _bloecke(css, "screen") + _bloecke(css, REDUZIERT)
    rest = css
    for a, b in sorted(bloecke, reverse=True):
        rest = rest[:a] + rest[b:]
    assert "pinnwand" not in rest


def test_reduzierte_bewegung_schaltet_drehungen_ab(css: str):
    block = _media(css, REDUZIERT)
    assert PINNWAND in block
    assert re.search(r"transform:\s*none\s*!important", block)
    assert re.search(r"transition:\s*none\s*!important", block)
