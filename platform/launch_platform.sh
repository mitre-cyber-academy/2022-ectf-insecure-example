#!/usr/bin/bash

# 2022 eCTF
# Stellaris platform launch script
# Jake Grycel
#
# (c) 2022 The MITRE Corporation
#
# This source file is part of an example system for MITRE's 2022 Embedded System
# CTF (eCTF). This code is being provided only for educational purposes for the
# 2022 MITRE eCTF competition, and may not meet MITRE standards for quality.
# Use this code at your own risk!
#
# DO NOT CHANGE THIS FILE

gdb_arg=""

# Parse args
while [ "$1" != "" ]; do
  case $1 in
    -u | --uart_sock )
        shift
        uart_sock=$1
        ;;
    -g | --gdb )
        gdb_arg="-gdb unix:/external_socks/gdb.sock,server"
        ;;
  esac
  shift
done

# Check required sockets
if [[ -z ${uart_sock} ]]; then
  echo "Please provide host socket"
  exit 1
fi

# Set up external emulator sockets
ext_sock_root="/external_socks"
ext_restart_sock="$ext_sock_root/restart.sock"
net_uart_sock="$uart_sock"

# Setup internal emulator sockets
int_sock_root="/internal_socks"
int_host_sock="$int_sock_root/host.sock"
int_restart_sock="$int_sock_root/restart.sock"
mkdir "$int_sock_root"

# Spin up the interface
python3 -u /platform/bl_interface.py --data-bl-sock "$int_host_sock" \
  --data-host-sock "$net_uart_sock" \
  --restart-bl-sock "$int_restart_sock" \
  --restart-host-sock "$ext_restart_sock" &

# Give time for the sockets and eFuse to initialize
sleep 2


# Spin up the emulator -- correct version (side-channel or not) is selected by makefile
qemu-system-arm -M lm3s6965evb -nographic -monitor none \
  ${gdb_arg} \
  -kernel /platform/bootstrapper_emu.elf \
  -serial unix:${int_host_sock} \
  -serial unix:${int_restart_sock}