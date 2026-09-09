#!/bin/bash
set -euo pipefail

OUTFILE="/etc/prometheus/targets/beowulf-nodes.yml"
NODES=$(puppetserver ca list --all \
  | grep -oP 'beowulf-\d+\.op\.ac\.nz' \
  | sort -u)

{
  echo "- targets:"
  for n in $NODES; do
    echo "    - ${n}:9100"
  done
  echo "  labels:"
  echo "    cluster: beowulf"
  echo "    role: worker"
} > "$OUTFILE"