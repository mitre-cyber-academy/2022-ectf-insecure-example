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

When running this code for the first time, you must pull the newest version of
the eCTF custom QEMU (emulator) for use in the challenge. Run the following to
get the appropriate emulator image:

```bash
docker pull ectf/ectf-qemu:tiva
```

## Creating and Launching a Deployment

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

### 3. Protect the SAFFIRe Files

We now need to protect the firmware and configuration files.
This can be done with the following commands:

```bash
python3 tools/run_saffire.py fw-protect --emulated \
    --sysname saffire-test \
    --fw-root firmware/ \
    --raw-fw-file example_fw.bin \
    --protected-fw-file example_fw.prot \
    --fw-version 2 \
    --fw-message 'hello world'
python3 tools/run_saffire.py cfg-protect --emulated \
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
python3 tools/run_saffire.py fw-update --emulated \
    --sysname saffire-test \
    --fw-root firmware/ \
    --uart-sock 1337 \
    --protected-fw-file example_fw.prot
python3 tools/run_saffire.py cfg-load --emulated \
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
python3 tools/run_saffire.py fw-readback --emualted \
    --sysname saffire-test \
    --uart-sock 1337 \
    --rb-len 100
python3 tools/run_saffire.py cfg-readback --emulated \
    --sysname saffire-test \
    --uart-sock 1337 \
    --rb-len 100
```

You may use a tool like xxd to verify that the output of the readback tool matches
the unprotected firmware.

### 6. Boot firmware

With firmware and configurations loaded onto the bootloader, we can now boot the device:

```bash
python3 tools/run_saffire.py boot --emulated \
    --sysname saffire-test \
    --uart-sock 1337 \
    --boot-msg-file boot.txt
python3 tools/run_saffire.py monitor --emulated \
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