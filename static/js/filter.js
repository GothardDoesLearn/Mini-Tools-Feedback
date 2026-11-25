// Filter der Methodenübersicht auf der Startseite (Issue #14). Einfaches JavaScript ohne
// Bibliotheken (ADR 0003). Ohne JavaScript ist die Filterleiste ausgeblendet und alle Karten
// bleiben sichtbar.
//
// Ablauf: zustandLesen() -> für jede Karte alle PRUEFUNGEN -> Karten ein-/ausblenden, Trefferzahl.
//
// ERWEITERUNGSPUNKT (Kategorie #15, URL #16, Zufall #17, Suche #18, Dauer #19):
//   1. Neue Angaben in zustandLesen() ergänzen (z. B. zustand.suche).
//   2. Eine Prüfung function (karte, zustand) -> true/false an PRUEFUNGEN anhängen.
//   3. Bei Änderung eines eigenen Bedienelements aktualisieren() aufrufen; beim Zurücksetzen
//      eigene Elemente in zuruecksetzen() leeren.
// Karten: { element, id, werte: { feld: [werte] } } aus data-methode / data-filter-<feld>.
(function () {
  "use strict";

  var formular = document.querySelector("[data-filterleiste]");
  if (!formular) return;

  var trefferzahl = document.querySelector("[data-trefferzahl]");
  var keineTreffer = document.querySelector("[data-keine-treffer]");
  var boxen = Array.prototype.slice.call(formular.querySelectorAll("input[type=checkbox]"));
  var felder = boxen
    .map(function (box) { return box.name; })
    .filter(function (feld, i, alle) { return alle.indexOf(feld) === i; });

  var karten = Array.prototype.slice.call(document.querySelectorAll("[data-methode]"))
    .map(function (element) {
      var werte = {};
      felder.forEach(function (feld) {
        var wert = element.getAttribute("data-filter-" + feld);
        werte[feld] = wert ? wert.split(" ") : [];
      });
      var kategorie = element.getAttribute("data-filter-kategorie");
      return {
        element: element,
        id: element.getAttribute("data-methode"),
        werte: werte,
        kategorien: kategorie ? kategorie.split(" ") : []
      };
    });

  // Kategorie-Auswahl (Issue #15): Buttons mit data-kategorie und aria-pressed, Mehrfachauswahl.
  // „Alle“ (data-kategorie="") ist gedrückt, wenn keine Kategorie gewählt ist, und hebt die
  // Auswahl auf.
  var kategorieKnoepfe = Array.prototype.slice.call(document.querySelectorAll("[data-kategorie]"));

  function istGedrueckt(knopf) {
    return knopf.getAttribute("aria-pressed") === "true";
  }

  function kategorienAnzeigen(gewaehlt) {
    kategorieKnoepfe.forEach(function (knopf) {
      var id = knopf.getAttribute("data-kategorie");
      var gedrueckt = id === "" ? gewaehlt.length === 0 : gewaehlt.indexOf(id) !== -1;
      knopf.setAttribute("aria-pressed", gedrueckt ? "true" : "false");
    });
  }

  function gewaehlteKategorien() {
    return kategorieKnoepfe
      .filter(function (knopf) { return knopf.getAttribute("data-kategorie") !== ""; })
      .filter(istGedrueckt)
      .map(function (knopf) { return knopf.getAttribute("data-kategorie"); });
  }

  kategorieKnoepfe.forEach(function (knopf) {
    knopf.addEventListener("click", function () {
      var id = knopf.getAttribute("data-kategorie");
      var gewaehlt = gewaehlteKategorien();
      if (id === "") {
        gewaehlt = [];
      } else if (gewaehlt.indexOf(id) !== -1) {
        gewaehlt.splice(gewaehlt.indexOf(id), 1);
      } else {
        gewaehlt.push(id);
      }
      kategorienAnzeigen(gewaehlt);
      aktualisieren();
    });
  });

  // Gewählte Werte je Filtergruppe: { feld: [werte] }; Gruppen ohne Haken fehlen.
  function zustandLesen() {
    var auswahl = {};
    boxen.forEach(function (box) {
      if (box.checked) (auswahl[box.name] = auswahl[box.name] || []).push(box.value);
    });
    return { auswahl: auswahl, kategorien: gewaehlteKategorien() };
  }

  // ODER innerhalb einer Gruppe, UND zwischen Gruppen.
  function passtZuFiltergruppen(karte, zustand) {
    return Object.keys(zustand.auswahl).every(function (feld) {
      return zustand.auswahl[feld].some(function (wert) {
        return karte.werte[feld].indexOf(wert) !== -1;
      });
    });
  }

  // ODER zwischen den gewählten Kategorien; keine Auswahl = alle.
  function passtZuKategorien(karte, zustand) {
    return zustand.kategorien.length === 0 || zustand.kategorien.some(function (id) {
      return karte.kategorien.indexOf(id) !== -1;
    });
  }

  var PRUEFUNGEN = [passtZuFiltergruppen, passtZuKategorien];

  function istGefiltert(zustand) {
    return Object.keys(zustand.auswahl).length > 0 || zustand.kategorien.length > 0;
  }

  function aktualisieren() {
    var zustand = zustandLesen();
    var anzahl = 0;
    karten.forEach(function (karte) {
      var sichtbar = PRUEFUNGEN.every(function (pruefe) { return pruefe(karte, zustand); });
      karte.element.hidden = !sichtbar;
      if (sichtbar) anzahl += 1;
    });
    if (trefferzahl) {
      trefferzahl.textContent = istGefiltert(zustand)
        ? anzahl + " von " + karten.length + " Methoden"
        : karten.length + " Methoden";
    }
    if (keineTreffer) keineTreffer.hidden = anzahl > 0;
  }

  function zuruecksetzen() {
    // Die Checkboxen leert der Browser selbst (type="reset"); erst danach neu filtern.
    kategorienAnzeigen([]);
    window.setTimeout(aktualisieren, 0);
  }

  formular.addEventListener("change", aktualisieren);
  formular.addEventListener("reset", zuruecksetzen);
  formular.addEventListener("submit", function (e) { e.preventDefault(); });
  aktualisieren();
})();
