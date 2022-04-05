# Instructions for the Reverse Engineering Challenge

## Aircraft Simulation Overview

During the attack phase, the avionic device that the attacker receives is the
Navigation Computer, which runs firmware that instructs the Autopilot how to
adjust the course to reach the destination. The Nav Computer does this by
getting the current location from the GPS, calculating a course adjustment based
on the installed flight configuration, and sending a heading update to the
Autopilot.

In addition to adjusting the course based on Nav Computer data, the Autopilot is
responsible for getting the current altitude from the Altimeter and lifting the
aircraft if it drops too low. In order to get the Aircraft Crash flag, attackers
will need to construct a malicious firmware that runs on the Nav Computer and
interferes with normal aircraft operation. The RE challenge will guide teams
towards implementing such a malicious firmware.

### Bus Packets

Every avionic device uses the same software driver to and and receive packets on
the bus. All packet types except *Data* packets are only accepted by the driver
if they are sent from a privileged device; at the start, the only privileged
device in the simulation is the Bus Controller.

**Bus Packet Types**

- Start
    - Start packets instruct the device application to run
- Shutdown
    - Shutdown packets instruct the device appliction to halt/shutdown
- Add Control
    - Add Control packets instruct devices to accept privileged commands from
      devices that were previously unprivileged
- Remove Control
    - Remove Control packets instruct devices to ignore privileged commands from
      devices that were previously privileged
- Data (Unprivileged)
    - Data packets are unprivileged and may be sent from any device to another
      device

**Note:** See `firmware_compiler/lib/bus.h` for the bus packet specification.


### Bus Devices

#### Bus Controller

The Bus Controller is the starting bus authority that can send privileged
commands. When the aircraft starts, the Bus Controller sends a start command to
all other devices, and periodically sends start commands to ensure that no
device becomes unresponsive.

#### Altimeter

The Altimeter senses the current altitude and sends it to the Autopilot at a
fixed interval. The Altimeter only reports the altitude while it is running.

#### GPS

When requested by the Nav Computer, the GPS sends the current latitude and
longitude to the Nav Computer.

#### Nav Computer

The Nav Computer receives the current location from the GPS and runs a
navigation algorithm to direct the aircraft towards the destination location.
The Nav Computer uses the current location and the destination stored in the
flight configuration to compute heading updates and send them to the Autopilot.

A starting point for the Nav Computer firmware has been provided in
`firmware_compiler/firmware.c`. It does not implement the full functionality of
the Nav Computer and does not use the correct device IDs. Use this to work on
the RE 2 Challenge firmware.

#### Autopilot

The Autopilot receives heading updates from the Nav Computer and adjusts the
aircraft path according to the updates. The Autopilot also receives the current
altitude from the altimeter and adjusts the aircraft altitude if it has flown
too low. Throughout the aircraft simulation, the altitude gradually decreases
and must periodically be adjusted by the Autopilot in order to not crash the
aircraft.


## RE 1 Challenge

For the first RE challenge, you will analyze the "firmware" running in the
Autopilot and recover the device IDs for the avionic bus devices. To get the
RE1 challenge flag, extract the following device IDs from
`firmware/re1_firmware.{elf,bin}`:

- Bus Controller ID
- NavComputer ID
- Altimeter ID
- Autopilot ID

To submit the flag, concatenate the device IDs together in the order listed,
using 16-bit lowercase hexadecimal format (4 hex characters per ID). For
example, if the IDs were 1000, 2000, 3000, 4000, respectively, the concatenated
hex value would be `03e807d00bb80fa0`. Submit your 16-character value to
scoreboard to get credit for this challenge.

*Note:* We have given you access to the functions called by the firmware. See
the `firmware_compiler` folder.


## RE 2 Challenge

In the second RE challenge, you will compile your own firmware that runs on the
Nav Computer and attempts to crash the aircraft. To do this, use the
`firmware_compiler` project included in this repo and modify the functionality
of `firmware.c` as you wish. When you think you have a firmware that can cause
the aircraft to crash, you will submit to the testing server to have your
firmware run with the aircraft simulation. Specific instructions to do this
submission will be given on Slack.

If the Autopilot is blocked from receiving the current altitude from the
Altimeter, it will not know to raise the aircraft altitude and eventually crash.
Successfully shutting down the Altimeter or Autopilot and preventing the Bus
Controller from turning it back on should be sufficient to cause the aircraft to
crash.