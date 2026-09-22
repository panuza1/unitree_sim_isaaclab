#!/usr/bin/env bash
set -u

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
# This project is deliberately run from the isolated unt_sim Conda environment.
# Permit PYTHON_BIN for automation, but never fall back to a repository virtualenv.
PYTHON_BIN=${PYTHON_BIN:-${SIM_PYTHON:-$(command -v python)}}
EXPECTED_PYTHON=$(readlink -f /home/admin/miniconda3/envs/unt_sim/bin/python)
# Isaac Sim on this ARM64 DGX requires the system OpenMP runtime to load
# before Kit.  Keep the setting scoped to this validator process tree.
if [[ -f /lib/aarch64-linux-gnu/libgomp.so.1 && ":${LD_PRELOAD:-}:" != *":/lib/aarch64-linux-gnu/libgomp.so.1:"* ]]; then
  export LD_PRELOAD="${LD_PRELOAD:+${LD_PRELOAD}:}/lib/aarch64-linux-gnu/libgomp.so.1"
fi
FAIL=0

pass() { printf '[PASS] %s\n' "$1"; }
warn() { printf '[WARN] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1"; FAIL=1; }

command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=name,driver_version --format=csv,noheader >/dev/null \
  && pass 'NVIDIA GPU/driver' || fail 'NVIDIA GPU/driver'
if [[ -x "$PYTHON_BIN" && "$(readlink -f "$PYTHON_BIN")" == "$EXPECTED_PYTHON" ]]; then
  pass 'Python environment (unt_sim)'
else
  fail "Python environment must be unt_sim ($EXPECTED_PYTHON); selected: $PYTHON_BIN"
fi
"$PYTHON_BIN" -c 'import isaacsim' >/dev/null 2>&1 && pass 'Isaac Sim' || fail 'Isaac Sim'
# isaaclab_tasks (and the project's tasks package) import USD bindings, which
# Isaac Sim exposes only after Kit starts; the runtime validator below covers
# that application-phase import.
"$PYTHON_BIN" -c 'import isaacsim; import isaaclab' >/dev/null 2>&1 && pass 'Isaac Lab' || fail 'Isaac Lab'
[[ -f assets/robots/g1-29dof-inspire-base-fix-usd/g1_29dof_with_inspire_rev_1_0.usd ]] \
  && pass 'G1 29DoF + Inspire assets' || fail 'G1 29DoF + Inspire assets'
[[ -f assets/objects/PackingTable/PackingTable.usd ]] \
  && pass 'PickPlace Cylinder assets' || fail 'PickPlace Cylinder assets'

if [[ "$FAIL" -eq 0 ]]; then
  if "$PYTHON_BIN" tools/validate_inspire_sim_mapping.py --headless --enable_cameras --device cuda; then
    # The validator starts Kit, imports tasks, and creates this exact Gym task.
    pass 'unitree_sim_isaaclab task registration'
    pass 'Inspire runtime joint mapping'
  else
    fail 'unitree_sim_isaaclab task registration'
    fail 'Inspire runtime joint mapping'
  fi
  if "$PYTHON_BIN" tools/test_inspire_sim_gestures.py --headless --enable_cameras --device cuda; then
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
