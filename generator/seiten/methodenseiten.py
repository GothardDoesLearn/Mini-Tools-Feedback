"""Methodenseiten /methoden/<id>/ (Issue #7; Kontext: generator/methodenseite.py)."""

from generator import methodenseite
from generator.content import SiteData
from generator.render import write_page
from generator.seiten import seite


@seite
def methodenseiten(env, output_dir, site: SiteData) -> None:
    for methode in site.methoden:
        write_page(
            env,
            output_dir,
            f"methoden/{methode.id}",
            "methode.html",
            **methodenseite.kontext(methode, site),
        )
