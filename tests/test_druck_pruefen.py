"""Reine Teile von tools/druck_pruefen.py (ohne Browser)."""

import struct
import zlib

import pytest

from tools.druck_pruefen import (
    DRUCKVORLAGEN_YAML,
    ansicht_einfuegen,
    erwartete_seiten,
    lies_druckvorlagen,
    pdf_seiten,
    png_zuschneiden,
)


@pytest.mark.parametrize(
    ("text", "erwartet"),
    [
        ("1", (1, 1)),
        ("3 (je Farbe 1)", (3, 3)),
        ("1–2", (1, 2)),
        ("2-4", (2, 4)),
        ("–", None),
        ("", None),
        ("ca. 2", None),
    ],
)
def test_erwartete_seiten(text, erwartet):
    assert erwartete_seiten(text) == erwartet


def test_lies_druckvorlagen():
    text = (
        "# Kommentar\n- id: a\n  titel: 'A'\n  seiten: '3 (je Farbe 1)'\n\n- id: b\n  seiten: '–'\n"
    )
    assert lies_druckvorlagen(text) == {"a": "3 (je Farbe 1)", "b": "–"}


def test_lies_druckvorlagen_echte_datei_hat_sollwerte():
    vorlagen = lies_druckvorlagen(DRUCKVORLAGEN_YAML.read_text(encoding="utf-8"))
    assert vorlagen
    assert all(text for text in vorlagen.values())


def _pdf(*objekte: str) -> bytes:
    return ("%PDF-1.4\n" + "".join(objekte) + "trailer\n%%EOF").encode()


def test_pdf_seiten_reihenfolge_ueber_kids_und_ausrichtung():
    daten = _pdf(
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        "2 0 obj\n<< /Type /Pages /Kids [4 0 R 3 0 R] /Count 2 >>\nendobj\n",
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] >>\nendobj\n",
        "4 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] >>\nendobj\n",
    )
    assert pdf_seiten(daten) == ["quer", "hoch"]


def test_pdf_seiten_erbt_mediabox_vom_elternknoten():
    daten = _pdf(
        "2 0 obj\n<</Type/Pages/Kids[3 0 R 4 0 R]/Count 2/MediaBox[0 0 842 595.5]>>\nendobj\n",
        "3 0 obj\n<</Type/Page/Parent 2 0 R>>\nendobj\n",
        "4 0 obj\n<</Type/Page/Parent 2 0 R>>\nendobj\n",
    )
    assert pdf_seiten(daten) == ["quer", "quer"]


def test_pdf_seiten_leer():
    assert pdf_seiten(b"%PDF-1.4\n%%EOF") == []


def test_ansicht_einfuegen_vor_ansicht_js():
    html = b'<!doctype html><html><head lang="de"><script src="/ansicht.js"></script></head>'
    neu = ansicht_einfuegen(html, "klar")
    assert neu.index(b'localStorage.setItem("mt-ansicht","klar")') < neu.index(b"ansicht.js")


def _png(breite: int, hoehe: int) -> bytes:
    """RGB-PNG, Pixel (x, y) = (x, y, 7); Zeilen abwechselnd mit Filter 0, 1 (Sub), 2 (Up)."""
    roh = bytearray()
    vorher = bytes(breite * 3)
    for y in range(hoehe):
        zeile = bytes(v for x in range(breite) for v in (x, y, 7))
        filt = y % 3
        if filt == 0:
            kodiert = zeile
        elif filt == 1:
            kodiert = bytes(
                (zeile[i] - (zeile[i - 3] if i >= 3 else 0)) & 0xFF for i in range(len(zeile))
            )
        else:
            kodiert = bytes((zeile[i] - vorher[i]) & 0xFF for i in range(len(zeile)))
        roh += bytes([filt]) + kodiert
        vorher = zeile

    def chunk(typ, daten):
        return (
            struct.pack(">I", len(daten)) + typ + daten + struct.pack(">I", zlib.crc32(typ + daten))
        )

    kopf = struct.pack(">IIBBBBB", breite, hoehe, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", kopf)
        + chunk(b"IDAT", zlib.compress(bytes(roh)))
        + chunk(b"IEND", b"")
    )


def _pixel(png: bytes) -> tuple[int, int, list[bytes]]:
    breite, hoehe = struct.unpack(">II", png[16:24])
    laenge = struct.unpack(">I", png[33:37])[0]
    roh = zlib.decompress(png[41 : 41 + laenge])
    zeilen = [roh[y * (breite * 3 + 1) + 1 : (y + 1) * (breite * 3 + 1)] for y in range(hoehe)]
    return breite, hoehe, zeilen


def test_png_zuschneiden():
    breite, hoehe, zeilen = _pixel(png_zuschneiden(_png(10, 9), 4, 5))
    assert (breite, hoehe) == (4, 5)
    for y, zeile in enumerate(zeilen):
        assert zeile == bytes(v for x in range(4) for v in (x, y, 7))


def test_png_zuschneiden_groesser_als_bild_bleibt_bildgroesse():
    breite, hoehe, _ = _pixel(png_zuschneiden(_png(3, 2), 100, 100))
    assert (breite, hoehe) == (3, 2)
