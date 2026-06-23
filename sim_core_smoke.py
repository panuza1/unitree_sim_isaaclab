#!/usr/bin/env python3
"""Minimal Isaac Sim runner: no DDS, no teleimager, no XR."""

import argparse
import os
import time

import gymnasium as gym
import torch
from isaaclab.app import AppLauncher


project_root = os.path.dirname(os.path.abspath(__file__))
os.environ["PROJECT_ROOT"] = project_root

parser = argparse.ArgumentParser(description="Minimal Unitree Isaac Sim smoke runner")
parser.add_argument("--task", default="Isaac-PickPlace-Cylinder-G129-Dex3-Joint")
parser.add_argument("--steps", type=int, default=0, help="0 means run until the app closes")
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("--stats_interval", type=float, default=5.0)
parser.add_argument("--render_interval", type=int, default=None)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import tasks  # noqa: E402,F401
from isaaclab_tasks.utils.parse_cfg import parse_env_cfg  # noqa: E402


def zero_action(env):
    shape = getattr(env.action_space, "shape", None)
    if shape:
        return torch.zeros(shape, device=env.device)
    joint_count = len(env.scene["robot"].data.joint_names)
    return torch.zeros(joint_count, device=env.device)


def main():
    env = None
    try:
        env_cfg = parse_env_cfg(args.task, device=args.device, num_envs=1)
        env_cfg.env_name = args.task
        env_cfg.seed = args.seed

        env = gym.make(args.task, cfg=env_cfg).unwrapped
        env.seed(args.seed)
        if args.render_interval is not None:
            env.sim.render_interval = max(1, int(args.render_interval))

        env.sim.reset()
        env.reset()

        action = zero_action(env)
        start = last = time.time()
        step = 0
        print("[smoke] started: no DDS, no teleimager, no XR", flush=True)

        with torch.inference_mode():
            while simulation_app.is_running() and (args.steps <= 0 or step < args.steps):
                env.step(action)
                step += 1
                now = time.time()
                if now - last >= args.stats_interval:
                    print(f"[smoke] steps={step} avg_hz={step / (now - start):.2f}", flush=True)
                    last = now

    finally:
        if env is not None:
            env.close()
        simulation_app.close()


if __name__ == "__main__":
    main()
