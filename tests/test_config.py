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
        'website_name: "Testseite"\ndomain: "https://test.example"\nbeschreibung: "Test"\n'
        'github_repo: "https://github.com/x/y"\nkontakt_email: "a@test.example"\n',
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


PFLICHTFELDER = (
    'website_name: "X"\nbeschreibung: "X"\n'
    'github_repo: "https://github.com/x/y"\nkontakt_email: "a@x.example"\n'
)


def test_domain_ist_optional_und_fehlt_dann_im_fusstext(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(PFLICHTFELDER, encoding="utf-8")
    config = load_config(config_file)
    assert config.domain == ""
    assert config.domain_anzeige == ""

    build(output_dir=tmp_path / "dist", config=config)

    html = (tmp_path / "dist" / "vorlagen" / "exit-ticket" / "index.html").read_text(
        encoding="utf-8"
    )
    assert '<p class="blatt__fuss">X</p>' in html


def test_domain_wird_ohne_schema_angezeigt(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        PFLICHTFELDER + 'domain: "https://feedback.x.example/"\n', encoding="utf-8"
    )

    assert load_config(config_file).domain_anzeige == "feedback.x.example"


@pytest.mark.parametrize(
    "domain", ["feedback.x.example", "https://x.example/feedback/", "https://x example"]
)
def test_domain_mit_pfad_oder_ohne_schema_bricht_ab(tmp_path: Path, domain: str):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(PFLICHTFELDER + f'domain: "{domain}"\n', encoding="utf-8")

    with pytest.raises(ValidationError, match="domain"):
        load_config(config_file)
