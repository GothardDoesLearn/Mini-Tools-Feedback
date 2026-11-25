"""Kategorieseiten /kategorien/<slug>/ (Issue #12)."""

from generator.content import SiteData
from generator.karten import karten
from generator.render import kurzbeschreibung, write_page
from generator.seiten import seite


@seite
def kategorieseiten(env, output_dir, site: SiteData) -> None:
    """Schreibt /kategorien/<slug>/ mit Beschreibung und allen Methoden der Kategorie."""
    alle_karten = karten(site)
    for kategorie in site.kategorien:
        write_page(
            env,
            output_dir,
            kategorie.url.strip("/"),
            "kategorie.html",
            aktiver_bereich="methoden",
            seitentitel=kategorie.titel,
            beschreibung=kurzbeschreibung(kategorie.beschreibung),
            kategorie=kategorie,
            karten=[k for k in alle_karten if k.kategorie.id == kategorie.id],
        )
