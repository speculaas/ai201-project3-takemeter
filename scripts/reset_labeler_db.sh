#!/usr/bin/env bash
# Backup labeler DB, remove it, and optionally import pre-labeled CSV.
set -euo pipefail
cd "$(dirname "$0")/.."

DB="labeler/items.db"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="labeler/items.db.backup-${STAMP}"

if [[ -f "${DB}" ]]; then
  cp "${DB}" "${BACKUP}"
  echo "Backed up ${DB} -> ${BACKUP}"
  rm -f "${DB}"
  echo "Removed ${DB}"
else
  echo "No existing ${DB} (fresh start)"
fi

if [[ "${1:-}" == "--import" ]]; then
  shift
  python3 scripts/import_prelabeled.py "$@"
  echo
  echo "Start labeler: cd labeler && ./run.sh"
else
  echo "Empty DB ready. Next:"
  echo "  python3 scripts/import_prelabeled.py --reset-db   # or import after ./run.sh"
  echo "  cd labeler && ./run.sh"
fi
