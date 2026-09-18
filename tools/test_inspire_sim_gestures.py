#!/usr/bin/env python3
"""DGX-only simulation gesture smoke test; never publishes robot DDS commands."""

import argparse
import sys

GESTURES = {
    "OPEN": 1.0,
    "HALF_CLOSE": 0.5,
    "POWER_GRASP": 0.15,
    "PINCH": 0.35,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default="Isaac-PickPlace-Cylinder-G129-Inspire-Joint")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--settle-steps", type=int, default=50)
    parser.add_argument("--num_envs", type=int, default=1)
    from isaaclab.app import AppLauncher

    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    app = AppLauncher(args).app
    env = None
    try:
        import gymnasium as gym
        import torch
        import tasks  # noqa: F401
        from isaaclab_tasks.utils.parse_cfg import parse_env_cfg
        from tools.inspire_mapping import resolve_inspire_joint_indices

        env_cfg = parse_env_cfg(args.task, device=args.device, num_envs=args.num_envs)
        env = gym.make(args.task, cfg=env_cfg).unwrapped
        env.reset()
        robot = env.scene["robot"]
        joint_indices = resolve_inspire_joint_indices(tuple(robot.data.joint_names))
        action_term = env.action_manager.get_term("joint_pos")
        action_joint_ids = tuple(int(index) for index in action_term.joint_ids)
        indices = tuple(action_joint_ids.index(index) for index in joint_indices)
        action = torch.zeros(
            (env.num_envs, env.action_manager.total_action_dim),
            device=env.device,
        )
        for name, level in (*GESTURES.items(), ("OPEN", 1.0)):
            action[:, list(indices)] = level
            for _ in range(args.settle_steps):
                _, _, terminated, truncated, _ = env.step(action)
                if bool(terminated.any()) or bool(truncated.any()):
                    env.reset()
            pos = robot.data.joint_pos[:, list(indices)]
            if not bool(torch.isfinite(pos).all()):
                raise AssertionError(f"{name}: non-finite joint state")
            print(f"{name}: PASS")
        print("RESULT: PASS")
        return 0
    except Exception as exc:
        print(f"RESULT: FAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        if env is not None:
            env.close()
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
