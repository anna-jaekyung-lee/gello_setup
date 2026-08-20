"""Is the MuJoCo sim really alive? Checks physics, not just the process.

pgrep is misleading here: launch_nodes' ZMQ server runs on a non-daemon thread
that keeps the process alive even after the viewer window dies. Only a physics
step proves the viewer loop is running.
"""
import sys
import time

import numpy as np

from gello.zmq_core.robot_node import ZMQClientRobot

try:
    r = ZMQClientRobot(port=6001, host="127.0.0.1")
    before = np.asarray(r.get_joint_state(), dtype=float).copy()
except Exception as e:
    print(f"DEAD: cannot reach sim on port 6001 ({e})")
    sys.exit(1)

probe = before.copy()
probe[0] += 0.15
r.command_joint_state(probe)
time.sleep(1.0)
after = np.asarray(r.get_joint_state(), dtype=float)
r.command_joint_state(before)  # put it back

if np.abs(after - before).max() > 0.01:
    print("ALIVE: physics stepping, viewer window is up (Cmd+Tab to 'mjpython')")
else:
    print("DEAD: process is up but physics is frozen -- the viewer window closed.")
    print("  Relaunch:  pkill -f launch_nodes.py")
    print("             .venv/bin/mjpython experiments/launch_nodes.py --robot sim_ur")
    sys.exit(1)
