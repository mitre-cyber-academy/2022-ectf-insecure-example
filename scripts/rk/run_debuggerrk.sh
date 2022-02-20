#!/bin/bash

# Go back to root
cd ../..

python3 tools/run_saffire.py launch-bootloader-gdb --emulated  \
    --sysname saffire-testrk \
    --sock-root socks/ \
    --uart-sock 1709

cd ../..
