#!/bin/python3

# 2022 eCTF
# Create images for bootstrappers
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

import argparse
from pathlib import Path

FLASH_SIZE = 256 * 1024
FLASH_FRONT_SIZE = 0x5800
IMAGE_BL_SIZE = 115 * 1024
EEPROM_SIZE = 2 * 1024


def main(eeprom_secret):

    # Input bootloader and EEPROM images
    source_bl = Path("/bootloader/bootloader.bin")
    source_eeprom = Path("/bootloader/eeprom.bin")

    # Output binaries
    out_phys_image = Path("/bootloader/phys_image.bin")

    # Read input binaries
    with open(source_bl, "rb") as fp:
        bl_data = fp.read()

    with open(source_eeprom, "rb") as fp:
        eeprom_data = fp.read()

    # Pad bootloader for phys_image.bin
    image_bl_pad_len = IMAGE_BL_SIZE - len(bl_data)
    image_bl_padding = bytes([0xFF] * image_bl_pad_len)
    image_bl_data = bl_data + image_bl_padding

    # Pad EEPROM
    eeprom_pad_len = EEPROM_SIZE - len(eeprom_data)
    eeprom_padding = bytes([0xFF] * eeprom_pad_len)
    eeprom_data = eeprom_data + eeprom_padding

    # Add EEPROM secret to end of EEPROM
    if len(eeprom_secret) > 64:
        exit(f"EEPROM secret too long ({len(eeprom_secret)} > 64")
    eeprom_secret_pad_len = 64 - len(eeprom_secret)
    eeprom_secret_padding = bytes([0xFF] * eeprom_secret_pad_len)
    final_eeprom_data = eeprom_data[0:EEPROM_SIZE-64] + bytes(eeprom_secret, 'latin-1') + eeprom_secret_padding

    # Create phys_image.bin
    image_data = image_bl_data + final_eeprom_data

    # Write output binary
    with open(out_phys_image, "wb") as fp:
        fp.write(image_data)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--eeprom-secret", type=str, required=True, help="Secret to place in EEPROM")
    args = parser.parse_args()
    main(args.eeprom_secret)
