#!/usr/bin/env python3
"""DGX-only runtime validation of G1 Inspire articulation ordering.

This file intentionally imports Isaac only after argument parsing and is not
run on the laptop.  It exits non-zero when the loaded USD does not expose the
expected twelve joint names.
"""

import argparse
import sys


def _print_mapping(runtime_joint_names):
    from tools.inspire_mapping import (
        LEFT_INSPIRE_JOINT_NAMES,
        RIGHT_INSPIRE_JOINT_NAMES,
        format_inspire_mapping,
    )

    right, left = format_inspire_mapping(runtime_joint_names)
    print("RIGHT INSPIRE")
    for index, name in right:
        print(f"{index} -> {name}")
    print("LEFT INSPIRE")
    for index, name in left:
        print(f"{index} -> {name}")
    assert len(right) == len(RIGHT_INSPIRE_JOINT_NAMES) == 6
    assert len(left) == len(LEFT_INSPIRE_JOINT_NAMES) == 6


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default="Isaac-PickPlace-Cylinder-G129-Inspire-Joint")
    parser.add_argument("--num_envs", type=int, default=1)
    parser.add_argument("--device", default="cuda")
    from isaaclab.app import AppLauncher

    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    app = AppLauncher(args).app
    try:
        import gymnasium as gym
        import torch
        import tasks  # noqa: F401
        from isaaclab_tasks.utils.parse_cfg import parse_env_cfg

        env_cfg = parse_env_cfg(args.task, device=args.device, num_envs=args.num_envs)
        env = gym.make(args.task, cfg=env_cfg).unwrapped
        env.reset()
        names = tuple(env.scene["robot"].data.joint_names)
        _print_mapping(names)
        if len(names) < 12:
            raise AssertionError(f"expected at least 12 articulation joints, got {len(names)}")
        if not torch.isfinite(env.scene["robot"].data.joint_pos).all():
            raise AssertionError("runtime joint positions contain NaN/Inf")
        print("RESULT: PASS")
        env.close()
        return 0
    except Exception as exc:
        print(f"RESULT: FAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
