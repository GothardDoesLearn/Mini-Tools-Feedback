"""Gemeinsame pytest-Einstellungen."""

import os
import shutil

import pytest


def pytest_sessionstart(session):
    """In der CI dürfen die JavaScript-Tests nicht still übersprungen werden.

    Lokal werden Tests, die Node.js brauchen, ohne Node übersprungen. In der CI (Umgebungsvariable
    CI gesetzt) bricht der Lauf stattdessen ab, damit ein fehlendes Node nicht als „grün“ durchgeht.
    """
    if os.environ.get("CI") and shutil.which("node") is None:
        pytest.exit(
            "Node.js fehlt in der CI – die JavaScript-Tests würden übersprungen.", returncode=1
        )
