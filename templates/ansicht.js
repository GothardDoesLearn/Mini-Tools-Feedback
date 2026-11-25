/* Ansichts-Umschalter (DESIGN.md): setzt die gespeicherte Ansicht vor dem ersten Rendern. */
(function () {
  var html = document.documentElement;
  var schluessel = "mt-ansicht";
  var erlaubt = ["pinnwand", "klar"];
  // Schriften der Ansicht vorab laden (parallel zum Stylesheet), sonst verschiebt der späte
  // Schriftwechsel das Layout (Lighthouse CLS, Issue #37). Muss zu static/css/site/00-schriften.css passen.
  var schriften = {
    pinnwand: [
      "caveat/caveat-latin-700-normal",
      "nunito/nunito-latin-400-normal",
      "nunito/nunito-latin-600-normal",
      "nunito/nunito-latin-700-normal",
    ],
    klar: [
      "inter/inter-latin-400-normal",
      "inter/inter-latin-500-normal",
      "inter/inter-latin-600-normal",
      "inter/inter-latin-700-normal",
    ],
  };

  function vorladen(ansicht) {
    var liste = schriften[ansicht] || [];
    for (var i = 0; i !== liste.length; i++) {
      var link = document.createElement("link");
      link.rel = "preload";
      link.as = "font";
      link.type = "font/woff2";
      link.crossOrigin = "anonymous";
      link.href = "/static/fonts/" + liste[i] + ".woff2";
      document.head.appendChild(link);
    }
  }

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
  vorladen(html.getAttribute("data-ansicht"));

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
