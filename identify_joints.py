"""Wiggle one joint at a time; the ID that lights up is that joint's servo ID."""
import time
import numpy as np
from gello.dynamixel.driver import DynamixelDriver

PORT = "/dev/tty.usbserial-FTBIN528"
IDS = list(range(1, 8))

d = DynamixelDriver(IDS, port=PORT, baudrate=57600)
for _ in range(10):
    d.get_joints()
ref = d.get_joints().copy()

print("\nMove ONE joint at a time (start with the BASE, then the gripper trigger).")
print("The ID showing ***MOVING*** is that joint's servo ID. Ctrl-C to stop.\n")
print("  " + "".join(f"  ID{i:<8}" for i in IDS))
try:
    while True:
        q = d.get_joints()
        delta = q - ref
        cells = []
        for i, dv in zip(IDS, delta):
            cells.append(f" {'***'+str(i)+'***' if abs(dv) > 0.15 else f'{dv:+6.2f}':>9}")
        print("\r  " + "".join(cells) + "   ", end="", flush=True)
        time.sleep(0.08)
except KeyboardInterrupt:
    print("\ndone")
