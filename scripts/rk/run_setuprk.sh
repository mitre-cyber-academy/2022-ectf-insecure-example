#!/bin/bash

# Go back to root
cd ../..

# Shut down the bootloader
python3 tools/run_saffire.py kill-system --emulated --sysname saffire-testrk


# Build Deployment
python3 tools/run_saffire.py build-system --emulated \
    --sysname saffire-testrk \
    --oldest-allowed-version 1

# Load Bootloader
python3 tools/run_saffire.py load-device --emulated --sysname saffire-testrk

# Launch Bootloader
python3 tools/run_saffire.py launch-bootloader --emulated  \
    --sysname saffire-testrk \
    --sock-root socks/ \
    --uart-sock 1709


