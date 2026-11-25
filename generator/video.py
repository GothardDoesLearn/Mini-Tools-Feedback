"""Videos auf der Methodenseite (Issue #9): Zwei-Klick-Einbettung nach ADR 0001.

Beim Bauen wird nur die Einbettungsadresse (youtube-nocookie) berechnet; geladen wird sie
erst nach dem Klick (static/js/video.js). Vorschaubilder kommen nie von YouTube.
"""

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from generator.content import Video

_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
}
EINBETTUNG = "https://www.youtube-nocookie.com/embed/{id}?autoplay=1"


@dataclass
class VideoAnzeige:
    titel: str
    url: str  # Original-Link („Auf YouTube ansehen“), funktioniert immer
    einbettung: str | None  # nur bei erkannten YouTube-Adressen
    youtube: bool


def youtube_id(url: str) -> str | None:
    """Video-ID aus gängigen YouTube-Adressen, sonst None."""
    teile = urlparse(url)
    host = (teile.hostname or "").lower()
    kandidat = None
    if host == "youtu.be":
        kandidat = teile.path.strip("/")
    elif host in _HOSTS:
        if teile.path == "/watch":
            kandidat = parse_qs(teile.query).get("v", [""])[0]
        else:
            treffer = re.match(r"^/(?:embed|shorts|live|v)/([^/]+)", teile.path)
            kandidat = treffer and treffer.group(1)
    return kandidat if kandidat and _ID.match(kandidat) else None


def anzeige(video: Video) -> VideoAnzeige:
    video_id = youtube_id(video.url)
    return VideoAnzeige(
        titel=video.titel,
        url=video.url,
        einbettung=EINBETTUNG.format(id=video_id) if video_id else None,
        youtube=video_id is not None,
    )
