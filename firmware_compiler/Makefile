#  2022 eCTF
#  Firmware Makefile
#  Jake Grycel
#
#  (c) 2022 The MITRE Corporation
#
# This source file is part of an example system for MITRE's 2022 Embedded System CTF (eCTF).
# This code is being provided only for educational purposes for the 2022 MITRE eCTF competition,
# and may not meet MITRE standards for quality. Use this code at your own risk!

# define the part type and base directory - must be defined for makedefs to work
PART=TM4C123GH6PM
CFLAGSgcc=-DTARGET_IS_TM4C123_RB1

# Uncomment to enable debug symbols
# DEBUG=1

# additional base directories
LIB_ROOT=lib
TIVA_ROOT=${LIB_ROOT}/tivaware

# add additional directories to search for source files to VPATH
VPATH+=${LIB_ROOT}
VPATH+=${TIVA_ROOT}

# add additional directories to search for header files to IPATH
IPATH+=${LIB_ROOT}
IPATH+=${TIVA_ROOT}

# Include common makedefs
include ${TIVA_ROOT}/makedefs

# this rule must come first in `all`
all: ${COMPILER}

# this must be the last build rule of `all`
all: ${COMPILER}/firmware.axf

# build libraries
${TIVA_ROOT}/driverlib/${COMPILER}/libdriver.a:
	${MAKE} -C ${TIVA_ROOT}/driverlib

tivaware: ${TIVA_ROOT}/driverlib/${COMPILER}/libdriver.a

# clean the libraries
clean_tivaware:
	${MAKE} -C ${TIVA_ROOT}/driverlib clean

# clean all build products
clean: clean_tivaware
	@rm -rf ${COMPILER} ${wildcard *~}

# create the output directory
${COMPILER}:
	@mkdir ${COMPILER}

# for each source file that needs to be compiled besides the file that defines `main`
${COMPILER}/firmware.axf: ${COMPILER}/bus.o
${COMPILER}/firmware.axf: ${COMPILER}/uart.o
${COMPILER}/firmware.axf: ${COMPILER}/firmware.o
${COMPILER}/firmware.axf: ${COMPILER}/startup_${COMPILER}.o
${COMPILER}/firmware.axf: ${TIVA_ROOT}/driverlib/${COMPILER}/libdriver.a


SCATTERgcc_firmware=${TIVA_ROOT}/firmware.ld
ENTRY_firmware=Firmware_Startup

# Include the automatically generated dependency files.
ifneq (${MAKECMDGOALS},clean)
-include ${wildcard ${COMPILER}/*.d} __dummy__
endif
