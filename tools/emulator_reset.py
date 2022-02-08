# 2022 eCTF
# Bootloader Restart Utility
# Jake Grycel
#
# (c) 2022 The MITRE Corporation
#
# This source file is part of an example system for MITRE's 2022 Embedded System
# CTF (eCTF). This code is being provided only for educational purposes for the
# 2022 MITRE eCTF competition, and may not meet MITRE standards for quality.
# Use this code at your own risk!

import argparse
import socket
import time
import os


def parse_args():
    parser = argparse.ArgumentParser(description="Emulated bootloader reset tool")

    parser.add_argument(
        "--restart-sock",
        help="Path to the local folder where the device sockets are located",
        required=True,
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Construct the socket and release message file paths
    restart_sfile = os.path.join(args.restart_sock)

    print("Restarting the bootloader...")

    # Send character over UART to trigger interrupt
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(restart_sfile)
        sock.send(b"E")
    time.sleep(2)
    print("Restarted bootloader...")


if __name__ == "__main__":
    main()
