# 2022 MITRE eCTF Challenge: Secure Avionics Flight Firmware Installation Routine (SAFFIRe)
This repository contains an example reference system for MITRE's 2022 Embedded System CTF
(eCTF) - see https://ectf.mitre.org/ for details. This code is incomplete, insecure, and 
does not meet MITRE standards for quality.  This code is being provided for educational 
purposes to serve as a simple example that meets the minimum functional requirements for 
the 2022 eCTF.  Use this code at your own risk!

## Getting Started
Please see the [Getting Started Guide](getting_started.md).

## Project Structure
The example code is structured as follows

* `bootloader/` - Contains everything to build the SAFFIRE bootloader. See [Bootloader README](bootloader/README.md).
* `configuration/` - Directory to hold raw and protected configuration images. The repo comes with an example unprotected configuration binary.
* `dockerfiles/` - Contains all Dockerfiles to build system.
* `firmware/` - Directory to contain raw and protected firmware images. The repo comes with an example unprotected firmware binary.
* `host-tools/` - Contains the host tools.
* `platform/` - Contains everything to run the avionic device.
* `tools/` - Miscellaneous tools to run and interract with SAFFIRe.
* `saffire.cfg` - An example option config file for running SAFFIRe

