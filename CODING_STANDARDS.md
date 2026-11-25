# Prüfregeln für Reviews

Gilt beim Review eines Diffs. Ruff, pytest und die CI prüfen das Mechanische; hier stehen nur Ermessensfragen.
Jede Regel nennt das Ziel und die Grenze. Ein Fund nennt die Regel und die Stelle.

## Inhalt gehört nach `content/`

Ziel: Der Betreiber ändert jeden Text, den eine Lehrkraft als Information liest, in `content/`, ohne Code anzufassen.

- **Inhalt** (gehört nach `content/`): alles, was über Methoden, Tools, Druckvorlagen oder die Website
  informiert. Beispiele: Hinweise wie die Tool-Freigabe (`tools.yaml` → `hinweis_freigabe`), Anleitungstexte,
  Satzanfänge einer Methode, Intro-Texte, Lizenz- und Rechtstexte.
- **Oberfläche** (darf im Template stehen): kurze Bedienwörter, die nichts Inhaltliches aussagen, z. B.
  „Drucken“, „Filter zurücksetzen“, Navigationseinträge, Feldbeschriftungen einer Druckvorlage laut
  `docs/DRUCKVORLAGEN.md`.
- Texte, die schon in `content/` stehen, werden gelesen statt kopiert. Eine Kopie im Template ist ein Fund,
  auch wenn sie heute wörtlich übereinstimmt (Beispiel: `generator/vorlagen.py` liest die Satzanfänge aus
  `www.md`).
- Grenzfälle (Meta-Beschreibungen, Fußzeile) als Fund melden und dem Betreiber zur Entscheidung vorlegen.

## Bearbeitungsstand an einer Stelle

- Etiketten und Hinweise zu `annahme`, `platzhalter` und `entwurf` kommen nur aus `generator/status.py`
  (`status_texte` in Templates). Eigene Texte oder `if status == …`-Kaskaden im Template sind ein Fund.
- Statuswerte als `Status`/`PLATZHALTER` aus `generator/content.py`, nicht als bare Zeichenkette.
- Ob eine Methode eine Druckvorlage „hat“, entscheidet nur `hat_druckvorlage` (`generator/karten.py`).

## Entwürfe kennzeichnen

Neue Texte, die ein Agent schreibt, sind Entwürfe bis zur Freigabe (AGENTS.md):

- in Markdown-Inhalten über `status: entwurf`, in YAML/Config mit dem Kommentar `# ENTWURF – vom Betreiber noch freizugeben.`
- im PR und im Issue aufgelistet. Ein neuer, nicht gekennzeichneter Text ist ein Fund.

## Spec-Treue statt eigener Produktentscheidungen

Wo PRD oder Ticket mehrdeutig sind, setzt der Code die vorsichtigste Lesart um und verweist auf ein Issue mit
Label `needs-triage`. Eine stillschweigend getroffene Produktentscheidung (z. B. andere URL-Form als im PRD,
zusätzliche Anzeige, die das PRD nicht nennt) ist ein Fund.

## Ohne JavaScript erreichbar

ADR 0003: Alle Inhalte bleiben ohne JavaScript erreichbar. Bedienelemente, die nur mit JavaScript funktionieren,
sind ohne JavaScript ausgeblendet (`html:not([data-js])`) oder haben einen Link als Rückfall.
