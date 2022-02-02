#!/bin/bash

# Go back to root
cd ../..

python3 tools/emulator_reset.py --restart-sock socks/restart.sock
