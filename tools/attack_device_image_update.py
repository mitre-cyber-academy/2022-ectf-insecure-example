# 2022 eCTF
# Attack-Phase Image Update Routine
# Jake Grycel
#
# (c) 2022 The MITRE Corporation
#
# This source file is part of an example system for MITRE's 2022 Embedded System
# CTF (eCTF). This code is being provided only for educational purposes for the
# 2022 MITRE eCTF competition, and may not meet MITRE standards for quality.
# Use this code at your own risk!

import argparse
from pathlib import Path
from serial import Serial
from serial.tools import list_ports


success_codes = [1, 2, 3, 5, 6, 7, 9, 10, 12, 13, 15, 18, 21, 22, 23]
error_codes = [4, 11, 14, 16, 17, 19, 20]

UPDATE_COMMAND = b"\x00"


# Wait for expected bootloader repsonse byte
# Exit if response does not match
def verify_resp(ser, print_out=True):
    resp = ser.read(1)
    while (resp == b"") or (not ord(resp) in (success_codes + error_codes)):
        resp = ser.read(1)
    if ord(resp) not in success_codes:
        print(f"Error. Bootloader responded with: {ord(resp)}")
        exit()
    if print_out:
        print(f"Success. Bootloader responded with code {ord(resp)}")

    return ord(resp)


# Run full application update
def image_update(in_file):

    # USAGE:
    #   1. Start this script
    #   2. Start the device
    #
    # This script finds the correct serial port by looking at an initial
    # list and waiting for a new entry to show up.
    # It then assumes that is the correct port and tries an update

    # Look for a serial port to open
    print("Looking for new serial port to open...")
    search = True
    orig_port_list = list_ports.comports()
    orig_len = len(orig_port_list)
    while search:
        new_port_list = list_ports.comports()
        new_len = len(new_port_list)
        if new_len == (orig_len + 1):
            for port in new_port_list:
                if port not in orig_port_list:
                    com_port = port.device
                    search = False
                    break
        elif new_len != orig_len:
            # Something changed, so we adapt
            orig_port_list = new_port_list
            orig_len = new_len

    # Keep trying to connect
    while 1:
        try:
            ser = Serial(com_port, 115200, timeout=2)
            ser.reset_input_buffer()
            break
        except Exception:
            pass

    print(f"Connected to bootloader on {com_port}")

    # Open protected image
    img_file = Path(in_file)
    if not img_file.exists():
        print(f"Image file {img_file} not found. Exiting")
        exit()

    with open(img_file, "rb") as image_fp:

        # Send update command
        print("Requesting update")
        ser.write(UPDATE_COMMAND)

        # Wait for initial status messages to synchronize
        resp = -1
        while resp != success_codes[2]:
            resp = verify_resp(ser)

        # Send image and verify each block success
        print("Update started")
        print("Sending image data")
        block_bytes = image_fp.read(16)
        count = 0
        while block_bytes != b"":
            if (count % 100) == 0:
                print(f"Sending block {count}")
            count += 1

            ser.write(block_bytes)
            verify_resp(ser, print_out=False)
            block_bytes = image_fp.read(16)

        # Wait for update finish
        print("\nListening for update status...\n")
        resp = -1
        while resp != success_codes[-1]:
            resp = verify_resp(ser)

        print("\nUpdate Complete!\n")


# Run in application mode
if __name__ == "__main__":

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", required=True, help="Path to the input binary")

    args = parser.parse_args()
    image_update(args.infile)
