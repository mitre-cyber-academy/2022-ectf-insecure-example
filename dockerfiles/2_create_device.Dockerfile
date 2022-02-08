# 2022 eCTF
# Device Packager Dockerfile
# Andrew Mirghassemi
#
# (c) 2022 The MITRE Corporation
#
# This source file is part of an example system for MITRE's 2022 Embedded System
# CTF (eCTF). This code is being provided only for educational purposes for the
# 2022 MITRE eCTF competition, and may not meet MITRE standards for quality.
# Use this code at your own risk!
#
# DO NOT MODIFY THIS FILE

ARG SYSNAME
ARG PARENT
FROM ${SYSNAME}/host_tools as host_tools

FROM ${PARENT}

RUN apk update && apk upgrade && apk add python3

# Add environment customizations here
# NOTE: do this first so Docker can used cached containers to skip reinstalling everything

# Keep bootloader and EEPROM binaries
COPY --from=host_tools /bootloader /bootloader

# Pull in rest of platform
ADD platform/ /platform

# Create emulator state folders
RUN mkdir /flash
RUN mkdir /eeprom

# Create padded binaries for the system bootstrappers
RUN python3 /platform/create_images.py
