"""tools/deploy.sh bricht bei falscher Konfiguration ab, bevor gebaut oder hochgeladen wird."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKRIPT = ROOT / "tools" / "deploy.sh"
BASH = shutil.which("bash")

pytestmark = pytest.mark.skipif(BASH is None, reason="bash nicht gefunden")


def starte(tmp_path, *args, **umgebung):
    env = {k: v for k, v in os.environ.items() if not k.startswith("DEPLOY_")}
    # Nie die echte deploy.env des Betreibers lesen.
    env["DEPLOY_ENV"] = str(tmp_path / "gibt-es-nicht.env")
    env.update(umgebung)
    return subprocess.run(
        [BASH, SKRIPT.as_posix(), *args],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )


def test_ohne_ziel_bricht_ab(tmp_path):
    r = starte(tmp_path)
    assert r.returncode != 0
    assert "DEPLOY_ZIEL fehlt" in r.stderr


def test_ziel_ohne_pfad_bricht_ab(tmp_path):
    r = starte(tmp_path, DEPLOY_ZIEL="benutzer@server")
    assert r.returncode == 2
    assert "benutzer@server:/pfad" in r.stderr


def test_unbekannte_methode_bricht_ab(tmp_path):
    r = starte(tmp_path, DEPLOY_ZIEL="b@s:/w", DEPLOY_METHODE="ftp")
    assert r.returncode == 2
    assert "rsync oder sftp" in r.stderr


def test_unbekannte_option_bricht_ab(tmp_path):
    r = starte(tmp_path, "--los", DEPLOY_ZIEL="b@s:/w")
    assert r.returncode == 2


def test_ziel_kommt_aus_env_datei(tmp_path):
    datei = tmp_path / "deploy.env"
    datei.write_text('DEPLOY_ZIEL="b@s:/w"\nDEPLOY_METHODE="ftp"\n', encoding="utf-8")
    r = starte(tmp_path, DEPLOY_ENV=str(datei))
    assert r.returncode == 2
    assert "rsync oder sftp" in r.stderr


def test_zugangsdaten_sind_ignoriert():
    zeilen = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "deploy.env" in zeilen
