// Drucken-Button: nur mit JavaScript sichtbar; ohne JavaScript bleibt der Hinweis auf Strg+P.
document.querySelectorAll("[data-drucken]").forEach((knopf) => {
  knopf.hidden = false;
  knopf.addEventListener("click", () => window.print());
});
document.querySelectorAll("[data-drucken-hinweis]").forEach((hinweis) => {
  hinweis.hidden = true;
});
