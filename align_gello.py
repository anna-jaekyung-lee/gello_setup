"""Live helper: pose GELLO into the sim's reset pose before running teleop."""
import time
import numpy as np
from gello.agents.gello_agent import GelloAgent

PORT = "/dev/tty.usbserial-FTBIN528"
RESET = np.deg2rad([0, -90, 90, -90, -90, 0])  # matches run_env.py reset_joints
TOL = 0.8  # run_env.py's max_joint_delta

agent = GelloAgent(port=PORT)
print("\nMove GELLO until every joint reads OK, then Ctrl-C and launch teleop.\n")
try:
    while True:
        q = agent.act({})[:6]
        d = q - RESET
        row = " ".join(
            f"j{i}:{'OK ' if abs(x) <= TOL else 'OFF'}{x:+5.2f}" for i, x in enumerate(d)
        )
        ready = "  <<< ALL ALIGNED" if np.abs(d).max() <= TOL else ""
        print(f"\r{row}{ready}   ", end="", flush=True)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\ndone")
