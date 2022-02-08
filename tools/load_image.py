# 2022 eCTF
# Physical Device Loader
# Kyle Scaplen
#
# (c) 2022 The MITRE Corporation
#
# This source file is part of an example system for MITRE's 2022 Embedded System
# CTF (eCTF). This code is being provided only for educational purposes for the
# 2022 MITRE eCTF competition, and may not meet MITRE standards for quality.
# Use this code at your own risk!
#
# DO NOT CHANGE THIS FILE

import argparse
import logging
from enum import Enum
from pathlib import Path
from serial import Serial
from serial.tools import list_ports
from serial.serialutil import SerialException


log = logging.getLogger(__name__)


APP_PAGES = 115
EEPROM_PAGES = 2
PAGE_SIZE = 1024
APP_SIZE = APP_PAGES * PAGE_SIZE
BLOCK_SIZE = 16
APP_BLOCKS = APP_SIZE // BLOCK_SIZE
EEPROM_SIZE = EEPROM_PAGES * PAGE_SIZE
EEPROM_BLOCKS = EEPROM_SIZE // BLOCK_SIZE
TOTAL_SIZE = APP_SIZE + EEPROM_SIZE
TOTAL_PAGES = APP_PAGES + EEPROM_PAGES
TOTAL_BLOCKS = APP_BLOCKS + EEPROM_BLOCKS


class Code(Enum):
    RequestUpdate = b"\x00"
    StartUpdate = b"\x01"
    UpdateInitFlashEraseOK = b"\x02"
    UpdateInitEEPROMEraseOK = b"\x03"
    UpdateInitEEPROMEraseError = b"\x04"
    AppBlockInstallOK = b"\x05"
    AppBlockInstallError = b"\x06"
    EEPROMBlockInstallOK = b"\x07"
    EEPROMBlockInstallError = b"\x08"
    AppInstallOK = b"\x09"
    AppInstallError = b"\x0a"


def get_serial_port():
    orig_ports = set(list_ports.comports())
    while True:
        ports = set(list_ports.comports())
        new_ports = ports - orig_ports

        if len(new_ports) == 1:
            new_port = new_ports.pop()
            return new_port.device

        orig_ports = ports


def verify_resp(ser: Serial, expected: Code):
    resp = ser.read(1)
    while resp == b"":
        resp = ser.read(1)

    assert Code(resp) == expected


def load(in_file):
    # USAGE:
    #   1. Start this script
    #   2. Start the device
    #
    # This script finds the correct serial port by looking at an initial
    # list and waiting for a new entry to show up.
    # It then assumes that is the correct port and tries an update

    # Look for a serial port to open
    log.info("Searching for serial port. Connect and Turn on device.")
    com_port = get_serial_port()

    # Keep trying to connect
    log.info(f"Connecting to serial port {com_port}...")
    while True:
        try:
            ser = Serial(com_port, 115200, timeout=2)
            ser.reset_input_buffer()
            break
        except SerialException:
            # Try until serial is ready to accept
            pass

    # Open firmware
    log.info("Reading image file...")
    fw_file = Path(in_file)
    if not fw_file.exists():
        log.error(f"Firmware file {fw_file} not found.")
        ser.close()
        return

    fw_data = fw_file.read_bytes()
    fw_size = len(fw_data)
    if fw_size != TOTAL_SIZE:
        log.error(f"Invalid image size 0x{fw_size:X}. Expected 0x{TOTAL_SIZE:X}.")
        ser.close()
        return

    # Wait for bootloader ready
    log.info("Requesting update...")
    ser.write(Code.RequestUpdate.value)
    try:
        verify_resp(ser, Code.StartUpdate)
    except AssertionError:
        log.error("Bootloader did not start an update")
        ser.close()
        return

    # Wait for Flash erase
    log.info("Waiting for Flash Erase...")
    try:
        verify_resp(ser, Code.UpdateInitFlashEraseOK)
    except AssertionError:
        log.error("Error while erasing Flash")
        ser.close()
        return

    # Wait for EEPROM erase
    log.info("Waiting for EEPROM Erase...")
    try:
        verify_resp(ser, Code.UpdateInitEEPROMEraseOK)
    except AssertionError:
        log.error("Error while erasing EEPROM")
        ser.close()
        return

    # Send data in 16-byte blocks
    log.info("Sending firmware...")
    total_bytes = len(fw_data)
    block_count = 0
    i = 0
    while i < total_bytes:
        if ((block_count + 1) % 100) == 0:
            log.info(f"Sending block {block_count+1} of {TOTAL_BLOCKS}...")
        block_bytes = fw_data[i : i + BLOCK_SIZE]

        ser.write(block_bytes)

        try:
            if block_count < APP_BLOCKS:
                verify_resp(ser, Code.AppBlockInstallOK)
            else:
                verify_resp(ser, Code.EEPROMBlockInstallOK)

            i += BLOCK_SIZE
            block_count += 1
        except AssertionError:
            log.error(f"Install failed at block {block_count+1}.")
            ser.close()
            return -1

    try:
        verify_resp(ser, Code.AppInstallOK)
    except AssertionError:
        log.error("Image Failed to Install")
        return -1
    else:
        log.info("Image Installed.")

    return 0


# Run in application mode
if __name__ == "__main__":
    # configure logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", required=True, help="Path to the input binary")
    args = parser.parse_args()

    # load the image
    load(args.infile)
