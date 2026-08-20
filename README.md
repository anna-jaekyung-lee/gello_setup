# GELLO → UR5 teleop

A calibrated [GELLO](https://wuphilipp.github.io/gello_site/) leader arm driving a UR5e,
built on [wuphilipp/gello_software](https://github.com/wuphilipp/gello_software).

This repo carries the calibration and tooling for **one specific hand-built GELLO** — the
servo mapping and joint offsets here will not match a different build. Upstream's original
documentation is preserved in [UPSTREAM_README.md](UPSTREAM_README.md).

| | |
|---|---|
| **Leader** | GELLO, 7× Dynamixel XL330-M288 @ 57600 baud |
| **Follower** | UR5e + Robotiq 2f85 (MuJoCo sim, real robot pending) |
| **Interface** | U2D2, FTDI serial `FTBIN528` |
| **Sim status** | Verified end-to-end |
| **Real robot** | Not yet tested |

---

## Quick start (simulation)

```bash
git clone -b main https://github.com/anna-jaekyung-lee/gello_setup.git
cd gello_setup
git submodule update --init --recursive     # ~1.4 GB of MuJoCo models

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
```

Then, in two terminals:

```bash
# terminal 1 — sim viewer (prefix with mjpython on macOS)
python experiments/launch_nodes.py --robot sim_ur

# terminal 2 — teleop
python teleop_sim.py
```

`teleop_sim.py` moves the sim to wherever GELLO already is, so there is no pose to hold.
On macOS, `./restart_sim.sh` relaunches the viewer.

## Quick start (real UR5)

```bash
python experiments/launch_nodes.py --robot ur --robot_ip <UR_IP>
python experiments/run_env.py --agent=gello
```

> [!WARNING]
> **Use `run_env.py` on hardware, never `teleop_sim.py`.** The sim script deliberately drops
> the start-position safety guard, so the follower jumps straight to the leader's pose. That is
> harmless in MuJoCo and dangerous on a real arm.

---

## The calibration

This is the part that took real measurement. It lives in `PORT_CONFIG_MAP` in
[`gello/agents/gello_agent.py`](gello/agents/gello_agent.py).

```python
# Servos are numbered in REVERSE along the chain:
# ID 7 = base ... ID 2 = wrist_3, ID 1 = gripper.
# Calibrated at start_joints = (0, -1.57, 1.57, -1.57, -1.57, 0)
"/dev/tty.usbserial-FTBIN528": DynamixelRobotConfig(
    joint_ids=(7, 6, 5, 4, 3, 2),
    joint_offsets=(
        4 * np.pi / 2,
        2 * np.pi / 2,
        2 * np.pi / 2,   # elbow — see note below
        2 * np.pi / 2,
        2 * np.pi / 2,
        2 * np.pi / 2,
    ),
    joint_signs=(1, 1, -1, 1, 1, 1),
    gripper_config=(1, 101, 94),
),
```

Three things here are specific to this build and easy to get wrong:

**The servo chain runs backwards.** ID 7 is at the base and ID 1 is the gripper, so
`joint_ids` counts *down*. Confirmed by full-range sweep, not assumed.

| Servo ID | 7 | 6 | 5 | 4 | 3 | 2 | 1 |
|---|---|---|---|---|---|---|---|
| **Sim joint** | shoulder_pan | shoulder_lift | **elbow** | wrist_1 | wrist_2 | wrist_3 | gripper |

**The elbow offset is `2*pi/2`, not `3*pi/2`.** Calibration originally produced `3*pi/2`,
which read **+89° with the arm physically straight** and pushed the top of its travel past the
UR5e's ±π elbow limit, clamping away ~29% of the range. Both symptoms came from the same
one-step offset error.

**The gripper is mapped tighter than it measures.** The trigger physically sweeps only
89.1–100.9° (11.8° total), but is mapped across just 101→94° so a light squeeze already reaches
fully closed. Mapping the full sweep left the gripper at ~28% travel in practice.

### Recalibrating

```bash
python scripts/gello_get_offset.py \
    --port <your-port> \
    --joint-ids 7 6 5 4 3 2 1 \
    --start-joints 0 -1.57 1.57 -1.57 -1.57 0
```

`--joint-ids` is a local addition — upstream hardcodes IDs `1..N` and cannot express a
reversed chain.

---

## Running on Linux vs macOS

The robot lives on a Linux PC; calibration was done on a Mac. What differs:

| | macOS | Linux |
|---|---|---|
| **`ur-rtde`** | won't build (needs CMake + Boost) | installs from wheel — **why the robot runs here** |
| **Serial port** | `/dev/tty.usbserial-FTBIN528` | `/dev/serial/by-id/usb-FTDI_…-if00-port0` |
| **Port discovery** | `--gello-port` required | auto-globbed by `run_env.py` |
| **Sim viewer** | `mjpython` (Cocoa main-thread rule) | plain `python` |
| **Serial access** | none needed | `sudo usermod -aG dialout $USER`, then re-login |

On Linux, the **only** config edit needed is the `PORT_CONFIG_MAP` key — change it to whatever
`ls /dev/serial/by-id/` reports. Everything else transfers unchanged.

---

## What is actually verified

| Item | State | Evidence |
|---|---|---|
| Servo ID mapping | ✅ Confirmed | Full-range sweep; every servo showed 1.1–4.1 rad travel |
| Joint offsets | ✅ Confirmed | Elbow bug found and fixed; straight GELLO now reads ≈0° |
| Gripper range | ✅ Confirmed | 11.8° sweep mapped for full closure |
| Sim tracking | ✅ Confirmed | All six joints track commands at ~100% |
| Joint signs | ⚠️ Casual only | Looked right in use; never swept joint-by-joint to the limits |
| Behaviour at joint limits | ⚠️ Untested | No deliberate test for offset wrap at range extremes |
| Anything on real hardware | ⚠️ Untested | — |

The two unverified rows are exactly the ones that bite on a real arm. Sweeping each joint to
its limits *in sim* closes both, and takes about fifteen minutes.

---

## Helper scripts

| Script | Purpose | Real robot? |
|---|---|---|
| `diagnose.py` | 40 s full-range sweep; per-servo travel, mapped sim travel, exact gripper limits | Yes — best single tool |
| `identify_joints.py` | Wiggle one joint, see which servo ID responds | Yes — for suspected mismaps |
| `test_wrists.py` | Sweeps sim wrists with no leader attached | Sim only |
| `sim_status.py` | Probes physics to prove the viewer is alive — `pgrep` reports a dead viewer as running | Sim only |
| `teleop_sim.py` | One-command sim teleop, no pose-holding | **Sim only — unsafe on hardware** |
| `restart_sim.sh` | Kills a stale viewer and relaunches (macOS) | Sim only |
| `align_gello.py` | Superseded by `teleop_sim.py` | — |

`sim_status.py` exists because the sim's ZMQ server runs on a non-daemon thread: when the
viewer window dies, the process stays alive and the port stays open, so `pgrep` and `lsof`
both report a healthy sim that is not simulating anything. Only a physics step proves it.

---

## Open items

- **Range scaling.** GELLO's reachable range is limited by its wiring and won't match the
  UR5's. Per-joint scaling would map usable leader travel onto the robot's range — a change to
  the agent, not a config tweak. Not started.
- **Gripper feel.** If it closes too eagerly, widen `94` toward `92`; if it won't close fully,
  narrow toward `96`.
- **Data recording.** `run_env.py` has a `SaveInterface` for capturing demonstrations.
  Untouched so far.

---

## Credit

Built on [GELLO](https://github.com/wuphilipp/gello_software) by Philipp Wu et al. (MIT).
Upstream docs: [UPSTREAM_README.md](UPSTREAM_README.md).
