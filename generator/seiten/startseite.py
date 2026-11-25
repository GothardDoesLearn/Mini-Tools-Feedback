"""Startseite / mit Kategorie-Auswahl, Filterleiste, Suche und allen Methodenkarten."""

from generator import paths
from generator.content import SiteData, load_startseite
from generator.karten import dauer_bereich, karten
from generator.render import write_page
from generator.seiten import seite
from generator.startseite import kategorie_auswahl
from generator.suche import suchindex


@seite
def startseite(env, output_dir, site: SiteData) -> None:
    write_page(
        env,
        output_dir,
        "",
        "index.html",
        aktiver_bereich="methoden",
        texte=load_startseite(paths.CONTENT_DIR),
        kategorien=kategorie_auswahl(site),
        karten=karten(site),
        # Gruppen mit eigenen Werten; Kategorie (quelle: kategorien.yaml) hat eigene Auswahl (#11)
        filtergruppen=[g for g in site.filter if g.werte],
        suchindex=suchindex(site),
        dauer_bereich=dauer_bereich(site),
    )
