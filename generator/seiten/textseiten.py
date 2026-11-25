"""Textseiten /<id>/ aus content/seiten/*.md (Issue #34)."""

from generator import paths
from generator.content import SiteData, load_seiten
from generator.render import write_page
from generator.seiten import seite

# Textseiten mit eigenem Menüpunkt in der Hauptnavigation (die übrigen nur im Fuß verlinkt).
SEITEN_MIT_MENUEPUNKT = {"ueber"}


@seite
def textseiten(env, output_dir, site: SiteData) -> None:
    for textseite in load_seiten(paths.CONTENT_DIR):
        bereich = textseite.id if textseite.id in SEITEN_MIT_MENUEPUNKT else ""
        write_page(
            env, output_dir, textseite.id, "seite.html", seite=textseite, aktiver_bereich=bereich
        )
