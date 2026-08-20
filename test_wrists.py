"""Sweep the sim's wrist joints with NO GELLO involved.

If the wrists move here, the sim is fine and the issue is on the GELLO side
(or the viewer was frozen). If they don't, the viewer is dead -- run sim_status.py.
"""
import time

import numpy as np

from gello.zmq_core.robot_node import ZMQClientRobot

r = ZMQClientRobot(port=6001, host="127.0.0.1")
home = np.array([0, -1.57, 1.57, -1.57, -1.57, 0, 0], dtype=float)

print("centering ...")
for _ in range(150):
    r.command_joint_state(home)
    time.sleep(0.01)

for idx, name in [(3, "wrist_1"), (4, "wrist_2"), (5, "wrist_3")]:
    print(f"sweeping sim joint {idx} ({name}) +-1.2 rad -- WATCH THE VIEWER")
    t0 = time.time()
    while time.time() - t0 < 6.0:
        q = home.copy()
        q[idx] += 1.2 * np.sin(2 * np.pi * 0.4 * (time.time() - t0))
        r.command_joint_state(q)
        time.sleep(0.01)
    settled = r.get_joint_state()[idx]
    print(f"   -> sim reports joint {idx} at {settled:+.3f} rad")

print("\nIf all three visibly moved, the sim is healthy.")
