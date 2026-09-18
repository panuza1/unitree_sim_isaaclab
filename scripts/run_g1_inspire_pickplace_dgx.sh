#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

PYTHON=${SIM_PYTHON:-$ROOT/.venv/bin/python}
DGX_IP=${DGX_IP:?set DGX_IP to the GB10 LAN address}
DDS_INTERFACE=${DDS_INTERFACE:?set DDS_INTERFACE to the GB10 LAN interface}

[[ -x "$PYTHON" ]] || { echo "missing simulator Python: $PYTHON" >&2; exit 2; }
[[ -f "$ROOT/assets/robots/g1-29dof-inspire-base-fix-usd/g1_29dof_with_inspire_rev_1_0.usd" ]] \
  || { echo "missing G1 Inspire USD under $ROOT/assets" >&2; exit 2; }
[[ -f "$ROOT/assets/objects/PackingTable/PackingTable.usd" ]] \
  || { echo "missing PackingTable USD under $ROOT/assets" >&2; exit 2; }

export UNITREE_DDS_INTERFACE="$DDS_INTERFACE"
exec "$PYTHON" sim_main.py \
  --headless \
  --device cuda \
  --task Isaac-PickPlace-Cylinder-G129-Inspire-Joint \
  --action_source dds \
  --enable_inspire_dds \
  --sim_dds_command_only \
  --public_ip "$DGX_IP" \
  --livestream_type 2 \
  --camera_include front_camera,left_wrist_camera,right_wrist_camera \
  --camera_exclude world_camera \
  "$@"
