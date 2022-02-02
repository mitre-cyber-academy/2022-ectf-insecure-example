#!/bin/bash

# Go back to root
cd ../..

# Protect and load saffire firmware
python3 tools/run_saffire.py fw-protect --emulated \
    --sysname saffire-testrk \
    --fw-root firmware/ \
    --raw-fw-file example_fw.bin \
    --protected-fw-file example_fw.prot \
    --fw-version 2 \
    --fw-message 'hello world'

# Protect and load saffire config
python3 tools/run_saffire.py cfg-protect --emulated \
    --sysname saffire-testrk \
    --cfg-root configuration/ \
    --raw-cfg-file example_cfg.bin \
    --protected-cfg-file example_cfg.prot

# Firmware Update
python3 tools/run_saffire.py fw-update --emulated \
    --sysname saffire-testrk \
    --fw-root firmware/ \
    --uart-sock 1709 \
    --protected-fw-file example_fw.prot

# Config load
python3 tools/run_saffire.py cfg-load --emulated \
    --sysname saffire-testrk \
    --cfg-root configuration/ \
    --uart-sock 1709 \
    --protected-cfg-file example_cfg.prot

# Firmware Readback
python3 tools/run_saffire.py fw-readback --emualted \
    --sysname saffire-testrk \
    --uart-sock 1709 \
    --rb-len 100

# Config Readback
python3 tools/run_saffire.py cfg-readback --emulated \
    --sysname saffire-testrk \
    --uart-sock 1709 \
    --rb-len 100

# # Boot firmware
python3 tools/run_saffire.py boot --emulated \
    --sysname saffire-testrk \
    --uart-sock 1709 \
    --boot-msg-file boot.txt

# # Launch monitor
python3 tools/run_saffire.py monitor --emulated \
    --sysname saffire-testrk \
    --uart-sock 1709 \
    --boot-msg-file boot.txt


