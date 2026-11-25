// Zwei-Klick-Einbettung (Issue #9, ADR 0001): erst der Klick auf die eigene Vorschau
// ersetzt sie durch den YouTube-Player (youtube-nocookie). Vorher keine Anfrage an YouTube.
document.querySelectorAll("[data-video-einbettung]").forEach((knopf) => {
  knopf.addEventListener("click", () => {
    const player = document.createElement("iframe");
    player.src = knopf.getAttribute("data-video-einbettung");
    player.title = knopf.getAttribute("data-video-titel") || "Video";
    player.setAttribute("allow", "autoplay; encrypted-media; picture-in-picture; fullscreen");
    player.setAttribute("allowfullscreen", "");
    player.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");
    player.setAttribute("class", "video__player");
    knopf.replaceWith(player);
    player.focus();
  });
});
