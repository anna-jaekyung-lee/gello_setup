#!/bin/bash
# Restart the MuJoCo sim viewer. RUN THIS IN YOUR OWN TERMINAL and leave the
# window open -- the viewer dies if its launching session goes away, and it
# also dies when the Mac sleeps (the OpenGL context is destroyed).
cd "$(dirname "$0")" || exit 1
pkill -f "launch_nodes.py" 2>/dev/null
sleep 1
echo "starting sim (Ctrl-C here to stop it)..."
exec .venv/bin/mjpython experiments/launch_nodes.py --robot sim_ur
