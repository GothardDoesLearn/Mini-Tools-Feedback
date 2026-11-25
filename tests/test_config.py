from pathlib import Path

import pytest
from pydantic import ValidationError

from generator.build import build
from generator.config import load_config


def test_werbung_ist_standardmaessig_aus():
    assert load_config().werbung_aktiv is False


def test_website_name_kommt_aus_der_konfiguration(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        'website_name: "Testseite"\ndomain: "https://test.example"\nbeschreibung: "Test"\n',
        encoding="utf-8",
    )

    build(output_dir=tmp_path / "dist", config=load_config(config_file))

    html = (tmp_path / "dist" / "index.html").read_text(encoding="utf-8")
    assert "<title>Testseite</title>" in html


def test_unbekannter_schluessel_in_konfiguration_bricht_ab(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        'website_name: "X"\ndomain: "https://x.example"\nwerbng_aktiv: true\n', encoding="utf-8"
    )

    with pytest.raises(ValidationError):
        load_config(config_file)
