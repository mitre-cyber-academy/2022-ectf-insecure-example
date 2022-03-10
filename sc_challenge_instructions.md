# Instructions for Running the Side-Channel Emulator

This tutorial will show you how to use the side-channel (SC) emulator to collect
side-channel traces from the microcontroller running an encryption algorithm.

## 0.a. Pull the SC Emulator

**Note: You only need to do this once on your server**

```bash
docker pull ectf/ectf-qemu:tiva_sc
```


## 0.b. Pull the SC Challenge Bootloader Image

**Note: You only need to do this once on your server**

You will need the SC challenge bootloader image from DockerHub to complete the
challenge. Pull the image with:

```bash
docker pull ectf/bootloader:sc
```


## 0.c. Tag a copy of the SC Challenge Bootloader Image

**Note: Each user who wants to run the challenge must do this once**

You will need to create a copy of the image by tagging it to use in your own
copy of the system. If you haven't already, choose a unique `sysname` that no
one else on your server is using so that your systems don't conflict (you should
be doing this in general whenever running SAFFIRe). Then, tag a copy for your
`sysname` using the following:

```bash
docker image tag ectf/bootloader:sc <sysname>/bootloader:sc
```

*Make sure to replace `<sysname>` with your chosen name*

**Note:** If you reuse the same `sysname` for a build of your own design, you will
need to re-run `docker image tag ectf/bootloader:sc <sysname>/bootloader:sc` the
next time you want to work on the SC challenge.


## 1.a. Clear Previous Emulator State

Before running the challenge bootloader with your chosen `sysname`, it is good
practice to remove old state in the emulated device to avoid unexpected
behavior. Run the following command with your chosen `sysname`:

```bash
python3 tools/run_saffire.py load-device --emulated \
    --sysname <sysname>
```

If you get an error saying `No such volume`, that is okay; it means the state
has already been cleared.

If you get an error saying `volume is in use`, kill the system first with:


```bash
python3 tools/run_saffire.py kill-system --sysname <sysname>
```

Then run the `load-device` command again.


## 1.b. Launch the Bootloader with the SC Emulator

Instead of the typical `launch-bootloader` target of `tools/run_saffire.py`, we
will use the `launch-bootloader-sc` target instead to run the device with the
SC emulator enabled. Choose a unique `uart-sock` port and run the following
command:

```bash
python3 tools/run_saffire.py launch-bootloader-sc --emulated \
    --sysname <sysname> \
    --sock-root socks/ \
    --uart-sock <uart-sock>
```

*Make sure to replace `<uart-sock>` and `<sysname>` with your chosen values!*


## 2. Follow SC Challenge Instructions

See the challenge PDF released through Slack for an overview of the challenge.
Here is a quick useful command reference.

### Generate Random Input Data

This will generate 128 random bytes and store them in a file called
`aes_input.bin` 

```bash
dd if=/dev/urandom of=aes_input.bin count=128 bs=1
```


### Send Data and Collect Traces from the Device

This will run the example SC collector script, sending the first 16 bytes of
`aes_input.bin` to the bootloader to be encrypted, collecting 200000
side-channel samples, and storing the samples in `aes_traces.dat`

```bash
python3 tools/sc_example.py --uart-sock <uart-sock> \
    --sc-sock socks/sc_probe.sock \
    --i-file aes_input.bin \
    --o-file aes_traces.dat \
    --byte-skip-count 0 \
    --num-samples 200000
```