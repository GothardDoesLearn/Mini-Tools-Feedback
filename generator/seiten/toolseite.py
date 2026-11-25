"""Toolseite /tools/ aus tools.yaml (Issue #13)."""

from generator.content import SiteData
from generator.render import write_page
from generator.seiten import seite


@seite
def toolseite(env, output_dir, site: SiteData) -> None:
    write_page(
        env,
        output_dir,
        "tools",
        "tools.html",
        aktiver_bereich="tools",
        tools=site.tools,
        tools_hinweis=site.tools_hinweis,
        methoden_titel={m.id: m.titel for m in site.methoden},
    )
