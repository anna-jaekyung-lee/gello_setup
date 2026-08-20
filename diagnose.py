"""Move every GELLO joint through its FULL range, plus fully open/close the
gripper. Reports how far each servo travelled and how far each sim joint would
travel -- pinpointing dead joints and giving exact gripper limits.
"""
import time
from collections import defaultdict

import numpy as np

from gello.agents.gello_agent import GelloAgent

PORT = "/dev/tty.usbserial-FTBIN528"
DURATION = 40.0

agent = GelloAgent(port=PORT)
robot = agent._robot
ids = list(robot._joint_ids)  # order the driver reads them in
SIM_NAMES = ["shoulder_pan", "shoulder_lift", "elbow", "wrist_1", "wrist_2", "wrist_3", "GRIPPER"]

raw_hist = defaultdict(list)
map_hist = defaultdict(list)

print(f"\nservo read order (index -> ID): {list(enumerate(ids))}")
print(f"\n>>> For {int(DURATION)}s: move EACH joint through its full range,")
print(">>> one at a time, and fully open/close the gripper. Go.\n")

t0 = time.time()
while time.time() - t0 < DURATION:
    raw = robot._driver.get_joints()
    mapped = agent.act({})
    for i, v in enumerate(raw):
        raw_hist[i].append(v)
    for i, v in enumerate(mapped):
        map_hist[i].append(v)
    left = DURATION - (time.time() - t0)
    print(f"\r  {left:4.1f}s left   raw={np.round(raw,2)}", end="", flush=True)
    time.sleep(0.02)

print("\n\n=== RAW SERVO TRAVEL (did the servo physically move?) ===")
for i in range(len(ids)):
    a = np.array(raw_hist[i])
    span = a.max() - a.min()
    flag = "  <-- DEAD / barely moved" if span < 0.25 else ""
    print(f"  index {i} = servo ID {ids[i]:<2}: travel {span:6.3f} rad "
          f"[{a.min():7.3f} .. {a.max():7.3f}]{flag}")

print("\n=== MAPPED -> SIM JOINT TRAVEL (what the sim receives) ===")
for i in range(len(map_hist)):
    a = np.array(map_hist[i])
    span = a.max() - a.min()
    flag = "  <-- SIM JOINT WON'T MOVE" if span < 0.25 else ""
    unit = "" if i < 6 else "  (0..1 normalized)"
    print(f"  sim joint {i} ({SIM_NAMES[i]:>14}): travel {span:6.3f} "
          f"[{a.min():7.3f} .. {a.max():7.3f}]{unit}{flag}")

g = np.array(raw_hist[len(ids) - 1])  # gripper servo = last in read order
print(f"\n=== GRIPPER (servo ID {ids[-1]}) ===")
print(f"  raw range: {np.rad2deg(g.min()):.1f} deg .. {np.rad2deg(g.max()):.1f} deg"
      f"  (span {np.rad2deg(g.max()-g.min()):.1f} deg)")
print(f"  suggested -> gripper_config=({ids[-1]}, "
      f"{np.rad2deg(g.max()):.0f}, {np.rad2deg(g.min()):.0f})")
print("  (swap the last two numbers if the sim gripper ends up inverted)")
