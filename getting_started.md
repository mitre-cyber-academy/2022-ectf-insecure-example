# 2022 MITRE eCTF Getting Started

## Creating Your Own Fork
We suggest you create a fork of this repo so that you can begin to develop
your solution to the eCTF. To do this, you must fork the repo, change your
fork to the `origin`, and then add the example repo as another remote.
Follow these steps below.

1. Clone the eCTF repository using ssh or https 
```bash
git clone https://github.com/mitre-cyber-academy/2022-ectf-insecure-example --recursive
``` 

2. Change the current origin remote to another name
```bash
git remote rename origin example
```

3. Fork the example repo on github or create a repository on another hosting service.
   **You probably want to make the repo private for now so that other teams
   cannot borrow your development ideas** 

5. Add the new repository as the new origin
```bash
git remote add origin <url>
```

You can now fetch and push as you normally would using `git fetch origin` and
`git push origin`. If we push out updated code, you can fetch this new code
using `git fetch example`.


## Environment Setup

### Development Server

The development servers provided for you have been set up with all the necessary
packages for building and running the SAFFIRe system with Docker. When running
this code for the first time, you must pull the newest version of the eCTF
custom QEMU (emulator) for use in the challenge. Run the following to get the
appropriate emulator image:

```bash
docker pull ectf/ectf-qemu:tiva
```

### Personal Computer / Virtual Machine

To run the system on your local machine for either the physical or emulated
device, you must install Docker and Python. Since the Docker image containing
the Tiva C emulator is only built for the `arm64` architecture, we do not
guarantee that you can run the emulated system on your own local machine for VM.

#### Installing Docker Desktop (Windows and Mac)

Windows users will install Docker Desktop on Windows following the instructions
on [this page](https://docs.docker.com/desktop/windows/install/). We recommend
using the WSL2 backend. Mac users will install Docker Desktop on Mac following
the instructions on [this page](https://docs.docker.com/desktop/mac/install/).

Once you download and run the installer, you should start Docker Desktop if it
does not start automatically and agree to the terms. *Note: Docker Desktop
requires that anyone using Docker Desktop as a part of their work in a large
organization needs to buy a license. This should not apply to any participants
since you are using it for educational and personal purposes.*

Once you have Docker Desktop installed, you will have to run it in the
background when running SAFFIRE. To be able to use Docker when running the
system, make sure that you have a command line environment that can run Docker
commands. This should be automatically set up in your `PATH` environment
variable, so running the SAFFIRe commands should work in Windows Command Prompt
and Powershell.

#### Installing Docker Engine (Linux)

Linux uses will install Docker Engine following the instructions on
[this page](https://docs.docker.com/engine/install/). Click on the link for your
Linux distribution and you will be brought to the specific instructions for
installing docker on your computer. Be sure to follow the
[post-installation instructions](https://docs.docker.com/engine/install/linux-postinstall/)
to set up your user with privileges to run Docker containers. This page also
contains instructions on how to start Docker engine automatically at startup,
but you can start it per-session with `sudo service docker start`.

#### Installing Python3

There are a number of ways to install Python 3 on your computer. Mac and Windows
users can install it directly from [https://www.python.org/downloads/], and
Linux users can install it through their system package manager. There are lots
of tutorials online for how to install Python 3. Another option is to use
[https://www.anaconda.com/products/individual](Anaconda) or
[https://docs.conda.io/en/latest/miniconda.html](Miniconda3), which are Python
distribution manager thats include multiple versions of python and an easy way
to set up different environments and install compatiable packages together.

#### Installing Code Composer Studio (for physical system only)

To debug the physical microcontroller you need to install Texas Instruments Code
Composer Studio (CCS). Download the installer from
[this page](https://www.ti.com/tool/CCSTUDIO) (scroll down to "Downloads", click
"Download options" for *CCSTUDIO*, then click the "single file installer" for
your OS). This will download as a compressed archive, which you must extract and
navigate into to find the installer.

When installing, you must accept the license agreement and then go through a
system check. If you have recently installed other programs that require a
restart, the CCS installer will suggest that you restart your computer.
Additionally, CCS may have package dependencies on Linux, which you can find on
[this page](https://software-dl.ti.com/ccs/esd/documents/ccsv11_linux_host_support.html).
Then, confirm the installation folder. We recommend that you keep the default.
Then, proceed with "Custom Installation".

You only need to enable support for the TM4C12x ARM Cortex-M4F core-based MCUs,
and click "next". Make sure the Segger J-Link debug probe is selected in the the
debug probes list and click "next". Then click "next" until the installation
starts. *At the end of installation on Linux*: you may have to run the USB cable
drivers with `sudo sh <path-to-ccs1110/ccs/install_scripts/install_drivers.sh`.

#### PySerial (for physical system only)

After installing Python 3 you will need to install the `pyserial` package. See
the documentation for the specific Python 3 installation you set up on how to
install this package.


## Creating and Launching a Deployment (Emulated)

To launch the example SAFFIRe system (**and earn the Boot Reference flag**),
follow these steps. **Note: you can change the values of these arguments.
Since all team members log in on the same user, you may end up interfering with
each other's containers. To avoid that, use different `--sysname` and
`--uart-sock` values. We recommend each team member choosing a unique socket for
`--uart-sock` for the duration of the design phase.**

These steps should work on the development servers we provide out of the box.
If you would like to use the physical hardware, you must follow the environment
set-up instructions and use the `--physical` flag in place of `--emulated`
(NOTE: the physical hardware is not supported in the initial code release).

Please refer to the technical specifications document for explanations of 
the commands and arguments.

### 1. Building the Deployment

A deployment (host-tools + bootloader) is created using:

```bash
python3 tools/run_saffire.py build-system --emulated \
    --sysname saffire-test \
    --oldest-allowed-version 1
```

This will create two Docker images based on the host-tools and bootloader in the
repo:

- saffire-test/host_tools
- saffire-test/bootloader


### 2. Launch the Bootloader

The bootloader must first be loaded:

```bash
python3 tools/run_saffire.py load-device --emulated --sysname saffire-test
```

Then, a directory should be made for the sockets, after which the bootloader can
be launched:

```bash
mkdir socks
python3 tools/run_saffire.py launch-bootloader --emulated  \
    --sysname saffire-test \
    --sock-root socks/ \
    --uart-sock 1337
```

There are two alternative variants to this step, controlled by replacing
the `launch-bootloader` argument.
To connect GDB to the bootloader, use `launch-bootloader-gdb`. This will
start QEMU up, pausing at the first instruction until GDB is connected. The command
will print the GDB command to use to connect to the system. **NOTE: The bootloader
will not run in this mode until GDB has been attached and starts the bootloader.**
If you run with GDB, you will have to open another terminal to run the host tools.

Alternatively, to see the output of the Docker container running QEMU, use
`launch-bootloader-interractive`. One case where this is helpful is if you are
unsure whether the host tools or GDB is connecting to the bootloader. Info messages
are printed in the bootloader container when processes connect and disconnect.
If you run in interactive mode, you will have to open another terminal to run
the host tools.

### 3. Protect the Avionic Device Files

We now need to protect the firmware and configuration files.
This can be done with the following commands:

```bash
python3 tools/run_saffire.py fw-protect \
    --sysname saffire-test \
    --fw-root firmware/ \
    --raw-fw-file example_fw.bin \
    --protected-fw-file example_fw.prot \
    --fw-version 2 \
    --fw-message 'hello world'
python3 tools/run_saffire.py cfg-protect \
    --sysname saffire-test \
    --cfg-root configuration/ \
    --raw-cfg-file example_cfg.bin \
    --protected-cfg-file example_cfg.prot
```

The release message passed to `fw_protect` must be formatted as shown above, as
the quotation marks are required for passing the full string into the protect
tool as one argument. The escaped quotation marks '' are there for that purpose.


### 4. Update and Load the Bootloader

Now that we have protected firmware and configuration images, we can
load them onto the device with the following commands:

```bash
python3 tools/run_saffire.py fw-update \
    --sysname saffire-test \
    --fw-root firmware/ \
    --uart-sock 1337 \
    --protected-fw-file example_fw.prot
python3 tools/run_saffire.py cfg-load \
    --sysname saffire-test \
    --cfg-root configuration/ \
    --uart-sock 1337 \
    --protected-cfg-file example_cfg.prot
```

After this, the bootloader should now be ready to handle readback and boot commands.

### 5. Readback

With firmware and configurations loaded onto the bootloader, we can now use the
readback functionality with the following commands:

```bash
python3 tools/run_saffire.py fw-readback \
    --sysname saffire-test \
    --uart-sock 1337 \
    --rb-len 100
python3 tools/run_saffire.py cfg-readback \
    --sysname saffire-test \
    --uart-sock 1337 \
    --rb-len 100
```

You may use a tool like xxd to verify that the output of the readback tool matches
the unprotected firmware.

### 6. Boot firmware

With firmware and configurations loaded onto the bootloader, we can now boot the device:

```bash
python3 tools/run_saffire.py boot \
    --sysname saffire-test \
    --uart-sock 1337 \
    --boot-msg-file boot.txt
python3 tools/run_saffire.py monitor \
    --sysname saffire-test \
    --uart-sock 1337 \
    --boot-msg-file boot.txt
```

This first command tells the SAFFIRe bootloader to launch the firmware, printing
the boot message to the file `boot.txt` (which remains in the Docker container).
If this is successful and a release message was printed, the second command will
launch and monitor the output of the rest of the airplane, simulating a flight.

**IF EVERYTHING WORKS PROPERLY, CHECK THE OUTPUT OF THE MONITOR COMMAND FOR A FLAG**


### 8. Restarting the Bootloader

Any time you want to perform a soft reset on the microcontroller to restart the
bootloader, you can do so with:

```bash
python3 tools/emulator_reset.py --restart-sock socks/restart.sock
```

If you specified a different socket root with `--sock-root` when running
`launch-bootloader`, make sure to replace `socks/restart.sock` with the correct
path when running the reset tool.


### 7. Shutting Down the Bootloader

When you're done with the bootloader or would just like to rebuild, you can do so
with:

```bash
python3 tools/run_saffire.py kill-system --emulated --sysname saffire-test
```


## Running SAFFIRe with the Physical Device

Running SAFFIRe on the physical device uses the same `run_saffire.py` commands
as the emulated system, with a few additional options. Follow these steps to
build the system, load the device, and start the bootloader. *Note: If you are
using an Anaconda or Miniconda-based Python 3 installation, you may have to use
`python` instead of `python3` while running these commands*.

### 1. Building the Deployment

Create the system using:

```bash
python3 tools/run_saffire.py build-system --physical \
    --sysname saffire-test \
    --oldest-allowed-version 1
```

This will create two Docker images based on the host-tools and bootloader in the
repo:

- saffire-test/host_tools
- saffire-test/bootloader

### 2.a. Install the Device Bootstrapper (First-Time-Setup)

In order to automatically load the bootloader on to the physical device, you
must first install the MITRE bootstrapper provided in the `platform` folder.
Start Code Composer Studio, which will ask you for a folder to set up a
workspace in. You can use the default option or provide your own; the workspace
will only be used to store debug and program load configuration files.

Once the workspace opens, go to `File -> New -> Target Configuration` to set up
a new board configuration. Rename it to `TivaConfig.ccxml`, and store it in your
workspace folder (uncheck the shared location box and enter your workspace
folder). After creating the file, an editor will open with a few device options.
Select "Stellaris In-Circuit Debug Interface" for the connection type, and "Tiva
TM4C123GH6PM" as the device. Then click "Save".

Next, go to `Run -> Debug Configurations`. Select "Code Composer Studio - Device
Debugging" on the left panel, and then click the "New Launch Configuration"
button above the left panel. In the main panel that opens, change the "Name" to
`bootstrapper_load`, and choose the `TivaConfiguration.ccxml` file as the
"Target Configuration"; you will have to navigate to it through the "File
System" button. Then, in the "Program" tab, edit the "Program" field to point to
`<ectf-repo-root/platform/bootstrapper.elf`, and make sure the "Loading
options" are set to "Load program".

In the "Target" tab, under the "Auto Run and Launch Options" category, check the
boxes for "Halt the target before any debugger access" and "Connect to the
target on debugger startup". Click the "Apply" button to save all these
settings. Finally, plug in the board, turn it on with the top switch, and click
"Debug". This will open up a debugger window and install the bootstrapper on the
board. You can then click the red square "Stop" button near the top of the
screen to exit the debug window.

If you ever need to re-install the bootstrapper for some reason (maybe you
corrupt the Flash memory containing the bootstrapper), you can plug in the
board, and go to `Run -> Load -> bootstrapper_load`. This will briefly open a
debug window, install the bootstrapper, and then close the debug view. Remember,
this step does not have to be run every time. As long as you have the
bootstrapper installed on the board, you can proceed directly from
`build-system` to `load-device`.

### 2.b. Load the SAFFIRe Bootloader

To load your SAFFIRe bootloader into the device, plug in the microcontroller,
turn it **OFF**, and run the load step:

```bash
python3 tools/run_saffire.py load-device --physical --sysname saffire-test
```

This will start the bootstrap loader which looks for a serial port to open. When
the tool prints a message to turn on the device, turn it on and wait for the
load process to complete. While loading, the bootstrap loader will print out the
name of the serial port it connected to, which you will need for the
`launch-bootloader` step. Take note of this and keep it for future use, since
the same device should have the same serial port name each time you plug it in.

If you shutdown and restart the device, you do not need to load the bootloader
again; the `load-device` step is only necessary when building a new bootlaoder.
At power-up, the bootstrapper will check if an update is requested and then
start the SAFFIRe bootloader, which is indicated by a blue LED turning on.

This step will also automatically copy SAFFIRe bootloader ELF to your local
files so you can load debug symbols into the CCS debugger. With the above
invocation it will be called `saffire-test-bootloader.elf.deleteme`.

### 2.c. Set Up the CCS Debugger (First-Time Setup)

You can use CCS to debug the bootloader running on the physical device; this
debugger is particularly useful because of its graphical interface and easy
access into all the system registers. The first time you debug on the physical
device, you need to create another debug configuration that loads the bootloader
binary symbols, but does not load the program itself (that is accomplished by
the bootstrapper).

Once again, go to `Run -> Debug Configurations`, click on "Code Composer
Studio - Device Debugging" on the left panel and click "New Launch
Configuration". Call this one `saffire_debug` and set `TivaConfiguration.ccxml`
as the target configuration. In the "Program" tab, set the "Program" to point
to the `saffire-test-bootloader.elf.deleteme`; *Note: You will have to make all
file types visible as the default file selector window will filter out the file
due to the `.deleteme`*. Then, set "Load symbols only" as the "Loading options".

In the "Target" tab, under the "Auto Run and Launch Options" category, check the
"Halt the target before any debugger access" and "Connect to the target on
debugger startup" boxes. You may set other options on this tab as you wish.

Finally, in the "Source" tab click the "Add..." button, select "File System
Directory" as the type, click "OK", set the target directory to
`<ectf-repo-root>/bootloader`, and check the "Search subfolders" box. This will
allow the debugger to find all the source files referenced in the bootloader ELF
file. Click "OK" to exit the window, click "Apply" in the main configuration
window, and click "Debug" to start a debug session. During this first time setup
you can instantly close the debug view with the square red "stop" button.

In the future, when the device is running, you can start the debugger by
clicking the dropdown arrow next to the bug icon at the top of the CCS window
and select `saffire_debug` to start the debugger.

### 3. Start the Bootloader Bridge

Since the bootstrapper launches the SAFFIRe bootloader automatically, the
`launch-bootloader` step for the physical device flow starts a bridge between
the device serial port and the UART socket that the host tools connect to. This
bridge will take up a terminal, so make sure to open another one to run any host
tools. Using the serial port printed out by the bootstrap loader, run this
command:

```bash
mkdir socks
python3 tools/run_saffire.py launch-bootloader --physical  \
    --sysname saffire-test \
    --uart-sock 1337 \
    --serial-port <device_serial_port_name>
```

### 4. Host Tools

The rest of the SAFFIRe steps are run using the exact same commands as shown in
the earlier emulated device flow. You can run them in a new terminal and they
will interact with the device over the bootloader bridge started in the previous
step. *Note: `tools/emulator_reset.py` will not work on the physical device. To
soft reset the bootloader, press button SW2 on the development board*.


## Automating SAFFIRe Operation

### Scripting

We recommend creating scripts to run multiple SAFFIRe commands in a row. Two
useful scripts to create could be called `run_setup.sh` that runs the
`kill-system`, `build-system`, `load-device`, and `launch-bootloader` steps, and
`run_tools.sh` that runs the rest of the steps. This will make it easy to run
the host tools alongside a bootloader that has been launched in GDB or interactive
mode.

### Automatic Arguments

`tools/run_saffire.py` is set up to optionally read arguments from a file. The
arguments used in the above example commands are replicated in the example
arguments file `saffire.cfg`. For example, to run the same `launch-bootloader`
shown above using the argument file, run the following:

```bash
python3 tools/run_saffire.py launch-bootloader @saffire.cfg --emulated
```

Using an argument file makes it easy to re-use the same arguments for multiple
commands to reduce typing and typos. You can create multiple argument files and
use them for different configurations and testing.

Finally, if you want to override an argument specified in an argument file you
can specify the argument at the end of the command. For example, to run the
following example but with a different socket number, use the following:

```bash
python3 tools/run_saffire.py launch-bootloader @saffire.cfg --uart-sock=1338
```


## Using the Debugger

By using the `launch-bootloader-gdb` command, you can easily attach GDB
to the bootloader. To see the output of the host tools in real time, you will
have to run the debugger and host tools in separate windows. 

**Note:** By default GDB will not find the bootloader source files. Once inside
a GDB session, run the following to point GDB to the sources:

```bash
(gdb) directory bootloader
```

Now, when you break or inspect the code, you will be able to view the C source
corresponding to the disassembly

**Quick GDB Reference:**

- Set a function breakpoint: `b <function_name>`
- Set a breakpoint at an address: `b *0x<memory_address>`
- View memory location: `x 0x<memory address>`
- Continue execution: `c` or `continue`
- Step one instruction: `si`
- View CPU registers: `info registers` or `i r`
- Disassemble current context: `disas`
- Disassemble arbitrary location: `disas 0x<memory_address>, +0x<number_of_locations_to_show>`
- Switch the layout to view the assembly: `layout asm`
- Quit GDB: `quit` -- you may have to hit `y` and press enter if it asks you confirm the exit
    - If the debugger is running and it is not hitting breakpoints Hit `CTRL-C` first to pause

There are plenty of resources online for how to use GDB, and your teammates and
advisors can likely give you tips as well.


## Docker tricks

To view all running Docker containers:
```
docker ps
```

To kill the Docker container with process ID 12345:
```
docker kill 12345
```

To kill all Docker containers (be aware not to kill the containers of others on the server):
```
docker kill $(docker ps -q)
```
You can streamline this by adding `alias dockerka='docker kill $(docker ps -q)'` to your `.bashrc`.

To run a command in the Docker container `test:deployment`:
```
docker run test:deployment echo "this echo command will be run in the container"
```

Docker can chew up disk space, so if you need to reclaim some, first clean up unused
containers and volumes
```
docker container prune
docker volume prune
```

If that isn't enough, you can clean up all containers and volumes:
```
docker container prune -a
docker volume prune -a
```
NOTE: these will remove all of the cached containers, so the next builds may take a longer time


## Helpful Tricks

The example code is set up to clean up the system state when running `kill-system`.
But, when you are developing and things break, these are some helpful commands
to have handy.

- **Kill all docker containers**: `docker kill $(docker ps -q)`
- **Remove all sockets**: `rm -rf socks/*`
- **Kill the process in your window**: `CTRL-C`
- **Suspend the process in your window**: `CTRL-Z`
  - **Note:** Make sure to kill the process after!