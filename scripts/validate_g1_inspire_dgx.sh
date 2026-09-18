#!/usr/bin/env bash
set -u

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
PYTHON=${SIM_PYTHON:-$ROOT/.venv/bin/python}
FAIL=0

pass() { printf '[PASS] %s\n' "$1"; }
warn() { printf '[WARN] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1"; FAIL=1; }

command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=name,driver_version --format=csv,noheader >/dev/null \
  && pass 'NVIDIA GPU/driver' || fail 'NVIDIA GPU/driver'
[[ -x "$PYTHON" ]] && pass 'Python environment' || fail "Python environment ($PYTHON)"
"$PYTHON" -c 'import isaacsim' >/dev/null 2>&1 && pass 'Isaac Sim' || fail 'Isaac Sim'
"$PYTHON" -c 'import isaaclab, isaaclab_tasks' >/dev/null 2>&1 && pass 'Isaac Lab' || fail 'Isaac Lab'
[[ -f assets/robots/g1-29dof-inspire-base-fix-usd/g1_29dof_with_inspire_rev_1_0.usd ]] \
  && pass 'G1 29DoF + Inspire assets' || fail 'G1 29DoF + Inspire assets'
[[ -f assets/objects/PackingTable/PackingTable.usd ]] \
  && pass 'PickPlace Cylinder assets' || fail 'PickPlace Cylinder assets'

if "$PYTHON" -c 'import tasks; import gymnasium as gym; assert gym.spec("Isaac-PickPlace-Cylinder-G129-Inspire-Joint")' >/dev/null 2>&1; then
  pass 'unitree_sim_isaaclab task registration'
else
  fail 'unitree_sim_isaaclab task registration'
fi

if [[ "$FAIL" -eq 0 ]]; then
  if "$PYTHON" tools/validate_inspire_sim_mapping.py --headless --device cuda; then
    pass 'Inspire runtime joint mapping'
  else
    fail 'Inspire runtime joint mapping'
  fi
  if "$PYTHON" tools/test_inspire_sim_gestures.py --headless --device cuda; then
    pass 'Inspire simulation gesture smoke test'
  else
    fail 'Inspire simulation gesture smoke test'
  fi
else
  warn 'runtime mapping and gesture checks skipped because a simulator prerequisite failed'
fi

if [[ -n "${UNITREE_DDS_INTERFACE:-}" ]]; then
  pass "DDS interface configured: $UNITREE_DDS_INTERFACE"
else
  warn 'UNITREE_DDS_INTERFACE not set; set it to the DGX LAN interface before network validation'
fi

if [[ "$FAIL" -eq 0 ]]; then
  echo DGX_SIM_READY
else
  echo DGX_SIM_NOT_READY
fi
exit "$FAIL"
