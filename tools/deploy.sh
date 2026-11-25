#!/usr/bin/env bash
# Baut die Website und lädt dist/ auf den eigenen Server. Anleitung: docs/DEPLOYMENT.md
#
#   tools/deploy.sh          bauen, testen, hochladen
#   tools/deploy.sh --probe  bauen, testen, nur anzeigen, was hochgeladen würde
#
# Ziel und Zugang kommen aus Umgebungsvariablen oder aus der lokalen, von Git ignorierten Datei deploy.env
# (Vorlage: deploy.env.beispiel; anderer Pfad über DEPLOY_ENV). Zugangsdaten gehören nie ins Repo.
set -euo pipefail

cd "$(dirname "$0")/.."

probe=0
case "${1:-}" in
  "") ;;
  --probe) probe=1 ;;
  *) echo "Unbekannte Option: $1 (erlaubt: --probe)" >&2; exit 2 ;;
esac

env_datei="${DEPLOY_ENV:-deploy.env}"
if [[ -f "$env_datei" ]]; then
  # shellcheck disable=SC1090
  source "$env_datei"
fi

: "${DEPLOY_ZIEL:?DEPLOY_ZIEL fehlt, z. B. benutzer@server.example:/var/www/feedback-tools (siehe deploy.env.beispiel)}"
DEPLOY_METHODE="${DEPLOY_METHODE:-rsync}"
DEPLOY_PORT="${DEPLOY_PORT:-22}"
ssh_optionen=(-p "$DEPLOY_PORT")
if [[ -n "${DEPLOY_SCHLUESSEL:-}" ]]; then
  ssh_optionen+=(-i "$DEPLOY_SCHLUESSEL")
fi

if [[ "$DEPLOY_ZIEL" != *:* ]]; then
  echo "DEPLOY_ZIEL braucht die Form benutzer@server:/pfad" >&2
  exit 2
fi
case "$DEPLOY_METHODE" in
  rsync|sftp) ;;
  *) echo "DEPLOY_METHODE muss rsync oder sftp sein, nicht: $DEPLOY_METHODE" >&2; exit 2 ;;
esac

python=python
for kandidat in .venv/Scripts/python .venv/bin/python; do
  if [[ -x "$kandidat" || -x "$kandidat.exe" ]]; then python="$kandidat"; break; fi
done

if grep -q "example\.org" config.yaml; then
  echo "Achtung: config.yaml enthält noch Platzhalter (example.org)." >&2
fi

"$python" build.py
"$python" -m pytest -q

ziel="${DEPLOY_ZIEL%/}/"
if [[ "$DEPLOY_METHODE" == rsync ]]; then
  rsync_optionen=(-rlzv --delete --checksum --chmod=D755,F644 -e "ssh ${ssh_optionen[*]}")
  if (( probe )); then rsync_optionen+=(--dry-run); fi
  rsync "${rsync_optionen[@]}" dist/ "$ziel"
else
  host="${DEPLOY_ZIEL%%:*}"
  pfad="${DEPLOY_ZIEL#*:}"
  befehle="cd ${pfad%/}
put -r dist/* ."
  if (( probe )); then
    echo "Würde per sftp ($host) ausführen:"
    echo "$befehle"
    exit 0
  fi
  sftp -P "$DEPLOY_PORT" ${DEPLOY_SCHLUESSEL:+-i "$DEPLOY_SCHLUESSEL"} -b - "$host" <<<"$befehle"
  echo "Hinweis: sftp löscht keine alten Dateien auf dem Server (siehe docs/DEPLOYMENT.md)."
fi
