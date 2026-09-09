#!/bin/bash
set -euo pipefail

OUTFILE="/etc/prometheus/targets/batcsg1-nodes.yml"
NODES=$(puppetserver ca list --all \
  | grep -oP 'batcsg1-(web|app|db)' \
  | sort -u)

{
  echo "- targets:"
  for n in $NODES; do
    echo "    - ${n}:9100"
  done
  echo "  labels:"
  echo "    cluster: batcsg1"
} > "$OUTFILE"