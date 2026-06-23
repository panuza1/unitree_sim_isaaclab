# Codex Context

## Goal

Use `unitree_sim_isaaclab` with `xr_teleoperate` and Meta Quest 3.

Current target:

1. Isaac Sim runs reliably.
2. Quest 3 can view Isaac Sim camera stream.
3. Then restore full teleoperation so Quest hand tracking controls G1 + Dex3 in simulation.

## Repos

Main paths on remote machine:

```bash
~/Documents/jeng/unitree_sim_isaaclab
~/Documents/jeng/xr_teleoperate
```

Important remotes:

```bash
unitree_sim_isaaclab: https://github.com/panuza1/unitree_sim_isaaclab.git
xr_teleoperate:       https://github.com/panuza1/xr_teleoperate.git
```

## What Already Works

`sim_core_smoke.py` runs Isaac Sim core without DDS and does not freeze.

Known good command:

```bash
cd ~/Documents/jeng/unitree_sim_isaaclab
conda activate unt_sim

python sim_core_smoke.py \
  --device cuda:0 \
  --enable_cameras \
  --task Isaac-PickPlace-Cylinder-G129-Dex3-Joint \
  --render_interval 2
```

Quest image path also works when running `sim_core_smoke.py --quest` plus `quest_viewer.py`.

Terminal 1:

```bash
cd ~/Documents/jeng/unitree_sim_isaaclab
conda activate unt_sim

python sim_core_smoke.py \
  --device cuda:0 \
  --enable_cameras \
  --task Isaac-PickPlace-Cylinder-G129-Dex3-Joint \
  --render_interval 2 \
  --quest
```

Terminal 2:

```bash
cd ~/Documents/jeng/xr_teleoperate/teleop
conda activate tv

python quest_viewer.py \
  --img-server-ip 10.61.6.62 \
  --input-mode hand \
  --display-mode ego
```

Quest URL:

```text
https://10.61.6.62:8012/?ws=wss://10.61.6.62:8012
```

Good sign from `quest_viewer.py`:

```text
Received camera config from server 10.61.6.62:60000
```

## Fixes Already Applied

In `unitree_sim_isaaclab/teleimager`:

- Removed IsaacSimCamera per-frame debug log spam.
- Fixed `logging_mp.getLogger` API usage to `logging_mp.get_logger`.

In `unitree_sim_isaaclab`:

- Added `sim_core_smoke.py`.
- Added `--quest` option to `sim_core_smoke.py` to start the teleimager Isaac Sim image server.
- Added DDS setup trace logs in `dds/dds_master.py`.

In `xr_teleoperate`:

- Added `teleop/quest_viewer.py` for Vuer/Quest viewing only, without robot DDS/control.

## Current Blocker

Full `sim_main.py` still freezes during DDS setup.

Command that reproduces:

```bash
cd ~/Documents/jeng/unitree_sim_isaaclab
conda activate unt_sim

python sim_main.py \
  --device cuda:0 \
  --enable_cameras \
  --task Isaac-PickPlace-Cylinder-G129-Dex3-Joint \
  --enable_dex3_dds \
  --robot_type g129 \
  --step_hz 30 \
  --render_interval 2 \
  --camera_write_interval 5
```

The log reaches:

```text
[DDSManager] register object 'rewards' success (category: No category)
[DDSManager] setup publisher start: g129
```

Then it hangs.

This identifies the hang point:

```text
dds/dds_create.py
  dds_manager.start_publishing(publish_names)

dds/dds_master.py
  obj.setup_publisher()

dds/g1_robot_dds.py
  self.publisher = ChannelPublisher("rt/lowstate", LowState_)
  self.publisher.Init()
```

So the current likely blocker is `ChannelPublisher("rt/lowstate", LowState_).Init()`.

## Next Small Step

Add a flag to skip only the G1 state publisher while keeping the G1 subscriber:

```text
--no_g1_state_pub
```

Expected temporary behavior:

- Sim should avoid hanging at `rt/lowstate` publisher init.
- Sim can still subscribe to G1 command topic `rt/lowcmd`.
- This proves whether `rt/lowstate` publisher is the only blocking DDS object.

Minimal code target:

```text
sim_main.py
dds/dds_create.py
```

Suggested behavior in `dds_create.py`:

```python
if args_cli.robot_type == "g129" or args_cli.robot_type == "h1_2":
    from dds.g1_robot_dds import G1RobotDDS
    g1_robot = G1RobotDDS()
    dds_manager.register_object("g129", g1_robot)
    if not args_cli.no_g1_state_pub:
        publish_names.append("g129")
    subscribe_names.append("g129")
```

Then test:

```bash
python sim_main.py \
  --device cuda:0 \
  --enable_cameras \
  --task Isaac-PickPlace-Cylinder-G129-Dex3-Joint \
  --enable_dex3_dds \
  --robot_type g129 \
  --step_hz 30 \
  --render_interval 2 \
  --camera_write_interval 5 \
  --no_g1_state_pub
```

If that passes DDS setup, continue isolating Dex3 publisher/subscriber if needed.

## Notes

- Do not use `--device cpu` for this task. It causes slow Fabric/USD fallback and UI freezes.
- Use `--device cuda:0`.
- For Quest URLs, do not use `127.0.0.1`; use the machine LAN IP, currently `10.61.6.62`.
- DDS is required for full robot control. It is not required for Quest image viewing.
