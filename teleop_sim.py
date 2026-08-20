"""Single-command GELLO -> MuJoCo teleop.

Unlike experiments/run_env.py, this does NOT require you to hold GELLO in a fixed
reset pose. The sim follower smoothly travels to wherever GELLO currently is, then
teleop begins. Safe because the follower is simulated -- do NOT reuse this approach
on the real UR5 without restoring run_env.py's start-position guard.
"""
import time
from dataclasses import dataclass

import numpy as np
import tyro

from gello.agents.gello_agent import GelloAgent
from gello.zmq_core.robot_node import ZMQClientRobot


@dataclass
class Args:
    gello_port: str = "/dev/tty.usbserial-FTBIN528"
    sim_host: str = "127.0.0.1"
    sim_port: int = 6001
    hz: float = 100.0
    approach_speed: float = 2.5
    """Ceiling on rad/s any joint moves while the sim travels to GELLO's pose."""
    approach_accel: float = 0.8
    """How fast the approach speed ramps up (rad/s^2). Starts gentle, then
    accelerates until it catches GELLO even if you're still moving it."""
    tol: float = 0.05
    """Approach finishes when every joint is within this many rad."""
    fake_gello: bool = False
    """Drive with a synthetic leader instead of hardware (for testing)."""


class FakeGello:
    """Stand-in leader that traces a slow arc, for testing without hardware."""

    def __init__(self, n):
        self.n = n
        self.t0 = time.time()

    def act(self, obs):
        t = time.time() - self.t0
        q = np.array([0, -1.57, 1.57, -1.57, -1.57, 0, 0], dtype=float)[: self.n]
        q[0] += 0.6 * np.sin(2 * np.pi * 0.15 * t)
        q[2] += 0.4 * np.sin(2 * np.pi * 0.2 * t)
        if self.n == 7:
            q[6] = 0.5 + 0.5 * np.sin(2 * np.pi * 0.3 * t)
        return q


def main(args: Args) -> None:
    robot = ZMQClientRobot(port=args.sim_port, host=args.sim_host)
    n = robot.num_dofs()
    print(f"sim connected on {args.sim_host}:{args.sim_port}, dofs={n}")

    agent = FakeGello(n) if args.fake_gello else GelloAgent(port=args.gello_port)

    dt = 1.0 / args.hz

    # --- Phase 1: sim travels to GELLO, tracking it live if it drifts ---
    print("sim approaching GELLO's current pose ... (hold GELLO roughly steady)")
    # Ramp an internal setpoint rather than chasing measured qpos: the sim's
    # position actuators lag their target, so feeding qpos back stalls the ramp.
    cmd = np.asarray(robot.get_joint_state(), dtype=float)
    t_start = time.time()
    while True:
        target = np.asarray(agent.act({}), dtype=float)
        delta = target - cmd
        worst = np.abs(delta).max()
        if worst <= args.tol:
            break
        if time.time() - t_start > 30:
            print(f"\n  still {worst:.3f} rad away after 30s -- starting anyway")
            break
        speed = min(
            args.approach_speed,
            0.15 + args.approach_accel * (time.time() - t_start),
        )
        cmd = cmd + delta * min(1.0, (speed * dt) / worst)
        robot.command_joint_state(cmd)
        print(f"\r  max delta {worst:6.3f} rad", end="", flush=True)
        time.sleep(dt)
    print("\naligned -- teleop live. Move GELLO. Ctrl-C to stop.")

    # --- Phase 2: teleop ---
    try:
        while True:
            loop_start = time.time()
            robot.command_joint_state(np.asarray(agent.act({}), dtype=float))
            time.sleep(max(0.0, dt - (time.time() - loop_start)))
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main(tyro.cli(Args))
