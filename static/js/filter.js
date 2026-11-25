// Filter der Methodenübersicht auf der Startseite (Issue #14). Einfaches JavaScript ohne
// Bibliotheken (ADR 0003). Ohne JavaScript ist die Filterleiste ausgeblendet und alle Karten
// bleiben sichtbar.
//
// Ablauf: zustandLesen() -> für jede Karte alle PRUEFUNGEN -> Karten ein-/ausblenden, Trefferzahl.
//
// ERWEITERUNGSPUNKT (Kategorie #15, URL #16, Zufall #17, Suche #18, Dauer #19):
//   1. Neue Angaben in zustandLesen() ergänzen (z. B. zustand.suche).
//   2. Eine Prüfung function (karte, zustand) -> true/false an PRUEFUNGEN anhängen.
//   3. Bei Änderung eines eigenen Bedienelements bedient() aufrufen (filtert + schreibt die URL);
//      beim Zurücksetzen eigene Elemente in zuruecksetzen() leeren.
//   4. Soll der Zustand in der URL stehen (teilbare Links, Zurück/Vor): EINE Zeile
//      urlParameter(...) ergänzen, siehe Abschnitt „Filterzustand in der URL“ unten.
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
      bedient();
    });
  });

  // Gewählte Werte je Filtergruppe: { feld: [werte] }; Gruppen ohne Haken fehlen.
  function zustandLesen() {
    var auswahl = {};
    boxen.forEach(function (box) {
      if (box.checked) (auswahl[box.name] = auswahl[box.name] || []).push(box.value);
    });
    var zustand = { auswahl: auswahl, kategorien: gewaehlteKategorien() };
    zustand.suche = suchbegriff();
    return zustand;
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
    return Object.keys(zustand.auswahl).length > 0 || zustand.kategorien.length > 0
      || zustand.suche !== "";
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
    if (zufallKnopf) zufallKnopf.disabled = anzahl === 0;
  }

  // Nach einer Bedienung neu filtern und den Zustand als Verlaufseintrag in die URL schreiben.
  function bedient() {
    aktualisieren();
    urlSchreiben("neu");
  }

  function zuruecksetzen() {
    // Die Checkboxen leert der Browser selbst (type="reset"); erst danach neu filtern.
    kategorienAnzeigen([]);
    if (suchfeld) suchfeld.value = "";
    window.setTimeout(bedient, 0);
  }

  // Volltextsuche (Issue #18) über Titel, Aliase und Anleitung. Den Index erzeugt der Build als
  // JSON (<script data-suchindex>). Groß-/Kleinschreibung und Akzente zählen nicht; bei mehreren
  // Wörtern muss jedes vorkommen. Ohne Suchfeld oder Index bleibt die Suche wirkungslos.
  var suchfeld = document.querySelector("[data-suche]");
  var suchtexte = {};

  function normalisieren(text) {
    return String(text).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }

  function suchbegriff() {
    return suchfeld ? suchfeld.value.trim() : "";
  }

  (function suchindexLaden() {
    var quelle = document.querySelector("[data-suchindex]");
    if (!quelle) return;
    try {
      JSON.parse(quelle.textContent).forEach(function (eintrag) {
        suchtexte[eintrag.id] = normalisieren(
          [eintrag.titel].concat(eintrag.aliase, [eintrag.text]).join(" | "));
      });
    } catch (fehler) {
      suchtexte = {};
    }
  })();

  function passtZurSuche(karte, zustand) {
    if (zustand.suche === "") return true;
    var text = suchtexte[karte.id] || "";
    return normalisieren(zustand.suche).split(/\s+/).every(function (wort) {
      return text.indexOf(wort) !== -1;
    });
  }

  PRUEFUNGEN.push(passtZurSuche);

  if (suchfeld) {
    // Beim Tippen keinen Verlaufseintrag pro Taste erzeugen, nur die URL ersetzen (#16).
    suchfeld.addEventListener("input", function () {
      aktualisieren();
      urlSchreiben("ersetzen");
    });
  }

  // „Zufällige Methode“ (Issue #17): wählt aus den gerade sichtbaren Karten.
  var zufallKnopf = document.querySelector("[data-zufall]");
  function zufaelligeMethodeOeffnen() {
    var treffer = karten.filter(function (karte) { return !karte.element.hidden; });
    if (treffer.length === 0) return;
    var wahl = treffer[Math.floor(Math.random() * treffer.length)];
    window.location.assign("/methoden/" + wahl.id + "/");
  }
  if (zufallKnopf) zufallKnopf.addEventListener("click", zufaelligeMethodeOeffnen);

  // Filterzustand in der URL (Issue #16), z. B. /?kategorie=A,D&form=digital.
  // Jede Bedienung erzeugt einen Verlaufseintrag (pushState), Zurück/Vor stellt ihn wieder her
  // (popstate). Ungültige Werte und leere Parameter werden ignoriert, die URL dann still
  // bereinigt (replaceState). Fremde Parameter bleiben erhalten.
  //
  // NEUER PARAMETER (z. B. Suche #18, Dauer #19) = EINE Zeile vor „Start“ unten:
  //   urlParameter("suche", function (z) { return z.suche ? [z.suche] : []; },
  //     function (werte) { suchfeld.value = werte[0] || ""; });
  // lesen(zustand) -> Liste von Texten ([] = Parameter fehlt; Wert aus zustandLesen()).
  // anwenden(werte) setzt die eigenen Bedienelemente ([] = Grundzustand) und ignoriert
  // ungültige Werte selbst. Mehrere Werte stehen kommagetrennt in der URL. Freitext (Suche):
  // beim Tippen aktualisieren() + urlSchreiben("ersetzen") statt bedient(), sonst entsteht pro
  // Tastendruck ein Verlaufseintrag.
  var URL_PARAMETER = [];

  function urlParameter(name, lesen, anwenden) {
    URL_PARAMETER.push({ name: name, lesen: lesen, anwenden: anwenden });
  }

  function kategorienAusUrl(werte) {
    var gueltig = kategorieKnoepfe.map(function (k) { return k.getAttribute("data-kategorie"); });
    kategorienAnzeigen(werte.filter(function (id) {
      return id !== "" && gueltig.indexOf(id) !== -1;
    }));
  }

  function filtergruppeAusUrl(feld) {
    return function (werte) {
      boxen.forEach(function (box) {
        if (box.name === feld) box.checked = werte.indexOf(box.value) !== -1;
      });
    };
  }

  urlParameter("kategorie", function (z) { return z.kategorien; }, kategorienAusUrl);
  felder.forEach(function (feld) {
    urlParameter(feld, function (z) { return z.auswahl[feld] || []; }, filtergruppeAusUrl(feld));
  });

  function dekodieren(text) {
    try {
      return decodeURIComponent(text.replace(/\+/g, " "));
    } catch (fehler) {
      return "";
    }
  }

  // "?a=1,2&b" -> [{ name: "a", roh: "a=1,2", werte: ["1", "2"] }, { name: "b", ... werte: [] }]
  function queryZerlegen(search) {
    return search.replace(/^\?/, "").split("&").filter(Boolean).map(function (teil) {
      var i = teil.indexOf("=");
      var name = dekodieren(i === -1 ? teil : teil.slice(0, i));
      var werte = i === -1 ? [] : teil.slice(i + 1).split(",").map(dekodieren).filter(Boolean);
      return { name: name, roh: teil, werte: werte };
    });
  }

  function istEigenerParameter(name) {
    return URL_PARAMETER.some(function (p) { return p.name === name; });
  }

  function queryBauen(zustand, search) {
    var teile = [];
    URL_PARAMETER.forEach(function (p) {
      var werte = p.lesen(zustand);
      if (werte.length) {
        teile.push(encodeURIComponent(p.name) + "=" + werte.map(encodeURIComponent).join(","));
      }
    });
    queryZerlegen(search).forEach(function (teil) {
      if (!istEigenerParameter(teil.name)) teile.push(teil.roh);
    });
    return teile.length ? "?" + teile.join("&") : "";
  }

  var verlauf = window.history && window.history.pushState ? window.history : null;

  function urlSchreiben(art) {
    if (!verlauf) return;
    var ort = window.location;
    var search = ort.search || "";
    var neu = queryBauen(zustandLesen(), search);
    if (neu === search) return;
    var url = ort.pathname + neu + (ort.hash || "");
    if (art === "ersetzen") verlauf.replaceState(null, "", url);
    else verlauf.pushState(null, "", url);
  }

  function ausUrlUebernehmen() {
    var teile = queryZerlegen((window.location && window.location.search) || "");
    URL_PARAMETER.forEach(function (p) {
      var werte = [];
      teile.forEach(function (teil) {
        if (teil.name === p.name) werte = werte.concat(teil.werte);
      });
      p.anwenden(werte);
    });
    aktualisieren();
    urlSchreiben("ersetzen");
  }

  urlParameter("suche", function (z) { return z.suche ? [z.suche] : []; }, function (werte) {
    if (suchfeld) suchfeld.value = werte.join(",");
  });

  // Start
  formular.addEventListener("change", bedient);
  formular.addEventListener("reset", zuruecksetzen);
  formular.addEventListener("submit", function (e) { e.preventDefault(); });
  if (window.addEventListener) window.addEventListener("popstate", ausUrlUebernehmen);
  ausUrlUebernehmen();
})();
