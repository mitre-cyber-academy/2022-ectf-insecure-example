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

from pathlib import Path

FLASH_SIZE = 256 * 1024
FLASH_FRONT_SIZE = 0x5800
IMAGE_BL_SIZE = 115 * 1024
EEPROM_SIZE = 2 * 1024


# Input bootloader and EEPROM images
source_bl = Path("/bootloader/bootloader.bin")
source_eeprom = Path("/bootloader/eeprom.bin")

# Output binaries
out_flash = Path("/flash/flash.bin")
out_eeprom = Path("/eeprom/eeprom.bin")
out_phys_image = Path("/bootloader/phys_image.bin")

# Read input binaries
with open(source_bl, "rb") as fp:
    bl_data = fp.read()

with open(source_eeprom, "rb") as fp:
    eeprom_data = fp.read()

# Pad front of bootloader for flash.bin
flash_front_padding = bytes([0xFF] * FLASH_FRONT_SIZE)
flash_front_data = flash_front_padding + bl_data

# Pad back bootloader for flash.bin
flash_back_pad_len = FLASH_SIZE - len(flash_front_data)
flash_back_padding = bytes([0xFF] * flash_back_pad_len)
flash_data = flash_front_data + flash_back_padding

# Pad bootloader for phys_image.bin
image_bl_pad_len = IMAGE_BL_SIZE - len(bl_data)
image_bl_padding = bytes([0xFF] * image_bl_pad_len)
image_bl_data = bl_data + image_bl_padding

# Pad EEPROM
eeprom_pad_len = EEPROM_SIZE - len(eeprom_data)
eeprom_padding = bytes([0xFF] * eeprom_pad_len)
eeprom_data = eeprom_data + eeprom_padding

# Create phys_image.bin
image_data = image_bl_data + eeprom_data

# Write output binaries
with open(out_flash, "wb") as fp:
    fp.write(flash_data)

with open(out_eeprom, "wb") as fp:
    fp.write(eeprom_data)

with open(out_phys_image, "wb") as fp:
    fp.write(image_data)
