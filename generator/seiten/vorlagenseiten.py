"""Druckvorlagen: Übersicht /vorlagen/ und je Vorlage /vorlagen/<id>/."""

from generator.content import PLATZHALTER, SiteData
from generator.paths import TEMPLATES_DIR
from generator.render import kurzbeschreibung, write_page
from generator.seiten import seite

# Layout einer Druckvorlage: templates/vorlagen/<id>.html (fehlt es: Seite „Vorlage folgt“).
VORLAGEN_LAYOUT_DIR = "vorlagen"


@seite
def vorlagen_uebersicht(env, output_dir, site: SiteData) -> None:
    write_page(
        env,
        output_dir,
        "vorlagen",
        "vorlagen.html",
        aktiver_bereich="vorlagen",
        druckvorlagen=[(v, site.methoden_mit_vorlage(v.id)) for v in site.druckvorlagen],
    )


@seite
def vorlagen(env, output_dir, site: SiteData) -> None:
    """Schreibt /vorlagen/<id>/ für jede Druckvorlage."""
    for vorlage in site.druckvorlagen:
        layout = f"{VORLAGEN_LAYOUT_DIR}/{vorlage.id}.html"
        gebaut = vorlage.status != PLATZHALTER and (TEMPLATES_DIR / layout).is_file()
        write_page(
            env,
            output_dir,
            f"vorlagen/{vorlage.id}",
            "vorlage.html",
            aktiver_bereich="vorlagen",
            seitentitel=f"{vorlage.titel} – Druckvorlage",
            beschreibung=kurzbeschreibung(f"Druckvorlage {vorlage.titel}: {vorlage.inhalt}"),
            vorlage=vorlage,
            methoden=site.methoden_mit_vorlage(vorlage.id),
            layout=layout if gebaut else None,
            hinweise=site.hinweise,
        )
