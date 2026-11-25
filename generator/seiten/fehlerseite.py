"""Fehlerseite /404.html (Links darin absolut)."""

from generator.content import SiteData
from generator.seiten import seite


@seite
def fehlerseite(env, output_dir, site: SiteData) -> None:
    (output_dir / "404.html").write_text(env.get_template("404.html").render(), encoding="utf-8")
