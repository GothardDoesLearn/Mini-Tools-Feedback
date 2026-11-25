/* Ansichts-Umschalter (DESIGN.md): setzt die gespeicherte Ansicht vor dem ersten Rendern. */
(function () {
  var html = document.documentElement;
  var schluessel = "mt-ansicht";
  var erlaubt = ["pinnwand", "klar"];

  function setze(ansicht) {
    if (erlaubt.indexOf(ansicht) === -1) ansicht = "pinnwand";
    html.setAttribute("data-ansicht", ansicht);
    var knoepfe = document.querySelectorAll("[data-ansicht-wahl]");
    for (var i = 0; i !== knoepfe.length; i++) {
      var an = knoepfe[i].getAttribute("data-ansicht-wahl") === ansicht;
      knoepfe[i].setAttribute("aria-pressed", an ? "true" : "false");
    }
  }

  var gespeichert = null;
  try {
    gespeichert = localStorage.getItem(schluessel);
  } catch (e) {}
  html.setAttribute("data-js", "");
  setze(gespeichert);

  document.addEventListener("DOMContentLoaded", function () {
    setze(html.getAttribute("data-ansicht"));
  });
  document.addEventListener("click", function (ereignis) {
    var knopf = ereignis.target.closest && ereignis.target.closest("[data-ansicht-wahl]");
    if (!knopf) return;
    var ansicht = knopf.getAttribute("data-ansicht-wahl");
    setze(ansicht);
    try {
      localStorage.setItem(schluessel, ansicht);
    } catch (e) {}
  });
  window.addEventListener("storage", function (ereignis) {
    if (ereignis.key === schluessel) setze(ereignis.newValue);
  });
})();
