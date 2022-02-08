# 2022 eCTF
# SAFFIRe Run Interface
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

import time
import argparse
import logging
import os
from pathlib import Path
import subprocess

import load_image
import serial_socket_bridge

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(name)-18s%(levelname)-8s %(message)s"
)
log = logging.getLogger(Path(__file__).name)


def make_dirs(dir_list):
    for path in dir_list:
        Path(path).mkdir(exist_ok=True)


def clear_dir(d):
    p = Path(d)
    if p.exists():
        for item in Path(d).iterdir():
            if item.is_dir():
                Path.rmdir(item)
            else:
                Path.unlink(item)


def get_volume(sysname, volume):
    return f"{sysname}-{volume}.vol"


def kill_system(args):
    # Stop running bootloader containers
    cmd = ["docker", "ps", "-q", "--filter", f"ancestor={args.sysname}/bootloader"]
    bl_container_ids = (
        subprocess.run(cmd, capture_output=True).stdout.decode("latin-1").rstrip()
    )
    if bl_container_ids != "":
        for cid in bl_container_ids.split("\n"):
            cmd = ["docker", "kill", f"{cid}"]
            subprocess.run(cmd)

    # Remove stopped bootloader containers
    cmd = [
        "docker",
        "ps",
        "-a",
        "-q",
        "--filter",
        f"ancestor={args.sysname}/bootloader",
    ]
    bl_container_ids = (
        subprocess.run(cmd, capture_output=True).stdout.decode("latin-1").rstrip()
    )
    if bl_container_ids != "":
        for cid in bl_container_ids.split("\n"):
            cmd = ["docker", "rm", f"{cid}"]
            subprocess.run(cmd)

    # Stop running host_tools containers
    cmd = ["docker", "ps", "-q", "--filter", f"ancestor={args.sysname}/host_tools"]
    host_container_ids = (
        subprocess.run(cmd, capture_output=True).stdout.decode("latin-1").rstrip()
    )
    if host_container_ids != "":
        for cid in host_container_ids.split("\n"):
            cmd = ["docker", "kill", f"{cid}"]
            subprocess.run(cmd)

    # Remove stopped host_tools containers
    cmd = [
        "docker",
        "ps",
        "-a",
        "-q",
        "--filter",
        f"ancestor={args.sysname}/host_tools",
    ]
    host_container_ids = (
        subprocess.run(cmd, capture_output=True).stdout.decode("latin-1").rstrip()
    )
    if host_container_ids != "":
        for cid in host_container_ids.split("\n"):
            cmd = ["docker", "rm", f"{cid}"]
            subprocess.run(cmd)

    log.info("All system containers stopped and removed")


def build_system(args):

    # Check for type
    if args.physical:
        parent = "alpine:3.12"
    elif args.emulated:
        parent = "ectf/ectf-qemu:tiva"
    else:
        exit("build_system: Missing '--emulated' or '--physical'")

    # Get Docker-managed volumes
    secrets_root = get_volume(args.sysname, "secrets")

    log.info("Removing system volumes (if they exist)")

    # Remove the old secrets
    cmd = ["docker", "volume", "rm", f"{secrets_root}"]
    subprocess.run(cmd)

    # Build host tools
    cmd = [
        "docker",
        "build",
        "--progress",
        "plain",
        ".",
        "-f",
        "dockerfiles/1_build_saffire.Dockerfile",
        "-t",
        f"{args.sysname}/host_tools",
        "--build-arg",
        f"OLDEST_VERSION={args.oldest_allowed_version}",
    ]
    subprocess.run(cmd)

    # Build device
    cmd = [
        "docker",
        "build",
        "--progress",
        "plain",
        ".",
        "-f",
        "dockerfiles/2_create_device.Dockerfile",
        "-t",
        f"{args.sysname}/bootloader",
        "--build-arg",
        f"SYSNAME={args.sysname}",
        "--build-arg",
        f"PARENT={parent}",
    ]
    subprocess.run(cmd)


def load_emulated_device(args):
    # Get Docker-managed volumes
    flash_root = get_volume(args.sysname, "flash")
    eeprom_root = get_volume(args.sysname, "eeprom")

    # Clear the Flash and EEPROM volumes so that new container has fresh state
    cmd = ["docker", "volume", "rm", f"{flash_root}"]
    subprocess.run(cmd)

    cmd = ["docker", "volume", "rm", f"{eeprom_root}"]
    subprocess.run(cmd)


def load_physical_device(args):
    # Copy bootloader physical image from device container
    cmd = ["docker", "create", f"{args.sysname}/bootloader"]
    container_id = (
        subprocess.run(cmd, capture_output=True).stdout.decode("latin-1").rstrip()
    )

    cmd = [
        "docker",
        "cp",
        f"{container_id}:bootloader/phys_image.bin",
        f"{args.sysname}-bl_image.bin.deleteme",
    ]
    subprocess.run(cmd)

    log.info(
        "Copied image to load into physical device:"
        f" {args.sysname}-bl_image.bin.deleteme"
    )

    # Copy bootloader ELF from device container
    cmd = [
        "docker",
        "cp",
        f"{container_id}:bootloader/bootloader.elf",
        f"{args.sysname}-bootloader.elf.deleteme",
    ]
    subprocess.run(cmd)

    log.info(f"Copied bootloader ELF: {args.sysname}-bootloader.elf.deleteme")

    cmd = ["docker", "rm", "-v", f"{container_id}"]
    subprocess.run(cmd)

    if load_image.load(f"{args.sysname}-bl_image.bin.deleteme") != 0:
        log.error("load_device: Physical device load failed'")
        exit(1)


def load_device(args):

    # Check for type
    if args.emulated:
        load_emulated_device(args)
    elif args.physical:
        load_physical_device(args)
    else:
        log.error("load_device: Missing '--emulated' or '--physical'")
        exit(1)
    log.info("Loaded SAFFIRe bootloader into device")


def launch_emulator(args, interactive=False, do_gdb=False):

    # Need abspath for local folder to mount as a Docker volume
    sock_root = os.path.abspath(args.sock_root)
    make_dirs([sock_root])

    # Get Docker-managed volumes
    flash_root = get_volume(args.sysname, "flash")
    eeprom_root = get_volume(args.sysname, "eeprom")

    gdb_arg = ""
    if do_gdb:
        gdb_arg = "--gdb"

    if interactive:
        dock_opt = "-i"
    else:
        dock_opt = "-d"

    log.info("Starting emulator")

    cmd = [
        "docker",
        "run",
        f"{dock_opt}",
        "-p",
        f"{args.uart_sock}:{args.uart_sock}",
        "--add-host=host.docker.internal:host-gateway",
        "-v",
        f"{sock_root}:/external_socks",
        "-v",
        f"{flash_root}:/flash",
        "-v",
        f"{eeprom_root}:/eeprom",
        f"{args.sysname}/bootloader",
        "sh",
        "/platform/launch_platform.sh",
        "--uart_sock",
        f"{args.uart_sock}",
        f"{gdb_arg}",
    ]
    subprocess.run(cmd)

    if do_gdb:
        # Copy bootloader.elf from the bootloader container to the local filesystem
        cmd = ["docker", "create", f"{args.sysname}/bootloader"]
        container_id = (
            subprocess.run(cmd, capture_output=True).stdout.decode("latin-1").rstrip()
        )

        cmd = [
            "docker",
            "cp",
            f"{container_id}:bootloader/bootloader.elf",
            f"{args.sysname}-bootloader.elf.deleteme",
        ]
        subprocess.run(cmd)

        log.info(f"Copied bootloader ELF: {args.sysname}-bootloader.elf.deleteme")

        cmd = ["docker", "rm", "-v", f"{container_id}"]
        subprocess.run(cmd)

        # Wait for a few seconds before connecting
        time.sleep(3)
        cmd = [
            "docker",
            "run",
            "-v",
            f"{sock_root}:/external_socks",
            f"{args.sysname}/bootloader",
            "chmod",
            "777",
            "/external_socks/gdb.sock",
        ]
        subprocess.run(cmd)

        print(
            "Launched bootloader with GDB.\n"
            "Run the following to attach to the GDB socket:\n"
            f"gdb-multiarch {args.sysname}-bootloader.elf.deleteme"
            f" -ex 'target remote {args.sock_root}/gdb.sock'"
        )


def launch_bootloader_bridge(args):
    # Launch bridge (takes up terminal)
    serial_socket_bridge.bridge(args.uart_sock, args.serial_port)


def launch_bootloader(args):
    # Check for type
    if args.emulated:
        if args.sock_root is None:
            log.error("launch_bootloader: Missing '--sock-root' for emulated flow")
            exit(1)
        launch_emulator(args)
    elif args.physical:
        if args.serial_port is None:
            log.error("launch_bootloader: Missing '--serial-port' for physical flow")
            exit(1)
        launch_bootloader_bridge(args)
    else:
        log.error("launch_bootloader: Missing '--emulated' or '--physical'")
        exit(1)


def launch_bootloader_gdb(args):
    if args.sock_root is None:
        log.error("launch_bootloader_gdb: Missing '--sock-root' for emulated flow")
        exit(1)
    launch_emulator(args, do_gdb=True)


def launch_bootloader_interactive(args):
    if args.sock_root is None:
        log.error(
            "launch_bootloader_interactive: Missing '--sock-root' for emulated flow"
        )
        exit(1)
    launch_emulator(args, interactive=True)


def fw_protect(args):
    # Get Docker-managed volumes
    secrets_root = get_volume(args.sysname, "secrets")

    # Need abspath for local folder to mount as a Docker volume
    fw_root = os.path.abspath(args.fw_root)
    make_dirs([fw_root])

    cmd = [
        "docker",
        "run",
        "-i",
        "--add-host=host.docker.internal:host-gateway",
        "-v",
        f"{secrets_root}:/secrets",
        "-v",
        f"{fw_root}:/firmware",
        f"{args.sysname}/host_tools",
        "/host_tools/fw_protect",
        "--firmware",
        f"{args.raw_fw_file}",
        "--version",
        f"{args.fw_version}",
        "--release-message",
        f"{args.fw_message}",
        "--output-file",
        f"{args.protected_fw_file}",
    ]
    subprocess.run(cmd)


def cfg_protect(args):
    # Get Docker-managed volumes
    secrets_root = get_volume(args.sysname, "secrets")

    # Need abspath for local folder to mount as a Docker volume
    cfg_root = os.path.abspath(args.cfg_root)
    make_dirs([cfg_root])

    cmd = [
        "docker",
        "run",
        "-i",
        "-v",
        f"{secrets_root}:/secrets",
        "-v",
        f"{cfg_root}:/configuration",
        f"{args.sysname}/host_tools",
        "/host_tools/cfg_protect",
        "--input-file",
        f"{args.raw_cfg_file}",
        "--output-file",
        f"{args.protected_cfg_file}",
    ]
    subprocess.run(cmd)


def fw_update(args):
    # Need abspath for local folder to mount as a Docker volume
    fw_root = os.path.abspath(args.fw_root)

    make_dirs([fw_root])

    cmd = [
        "docker",
        "run",
        "-i",
        "--add-host",
        "saffire-net:host-gateway",
        "-v",
        f"{fw_root}:/firmware",
        f"{args.sysname}/host_tools",
        "/bin/bash",
        "-c",
        f"rm -rf /secrets; "
        f"/host_tools/fw_update "
        f"--socket {args.uart_sock} "
        f"--firmware-file {args.protected_fw_file}",
    ]
    subprocess.run(cmd)


def cfg_load(args):
    # Need abspath for local folder to mount as a Docker volume
    cfg_root = os.path.abspath(args.cfg_root)

    make_dirs([cfg_root])

    cmd = [
        "docker",
        "run",
        "-i",
        "--add-host",
        "saffire-net:host-gateway",
        "-v",
        f"{cfg_root}:/configuration",
        f"{args.sysname}/host_tools",
        "/bin/bash",
        "-c",
        f"rm -rf /secrets ; "
        f"/host_tools/cfg_load "
        f"--socket {args.uart_sock} "
        f"--config-file {args.protected_cfg_file}",
    ]
    subprocess.run(cmd)


def readback(args, rb_region):
    # Get Docker-managed volumes
    secrets_root = get_volume(args.sysname, "secrets")

    cmd = [
        "docker",
        "run",
        "-i",
        "--add-host",
        "saffire-net:host-gateway",
        "-v",
        f"{secrets_root}:/secrets",
        f"{args.sysname}/host_tools",
        "/host_tools/readback",
        "--socket",
        f"{args.uart_sock}",
        "--region",
        f"{rb_region}",
        "--num-bytes",
        f"{args.rb_len}",
    ]
    subprocess.run(cmd)


def fw_readback(args):
    readback(args, rb_region="firmware")


def cfg_readback(args):
    readback(args, rb_region="configuration")


def boot(args):
    # Get Docker-managed volumes
    msg_root = get_volume(args.sysname, "messages")

    cmd = [
        "docker",
        "run",
        "-i",
        "--add-host",
        "saffire-net:host-gateway",
        "-v",
        f"{msg_root}:/messages",
        f"{args.sysname}/host_tools",
        "/bin/bash",
        "-c",
        f"rm -rf /secrets; "
        f"/host_tools/boot "
        f"--socket {args.uart_sock} "
        f"--release-message-file {args.boot_msg_file}",
    ]
    subprocess.run(cmd)


def monitor(args):
    # Get Docker-managed volumes
    msg_root = get_volume(args.sysname, "messages")

    cmd = [
        "docker",
        "run",
        "-i",
        "--add-host",
        "saffire-net:host-gateway",
        "-v",
        f"{msg_root}:/messages",
        f"{args.sysname}/host_tools",
        "/bin/bash",
        "-c",
        f"rm -rf /secrets ; "
        f"/host_tools/monitor "
        f"--socket {args.uart_sock} "
        f"--release-message-file {args.boot_msg_file}",
    ]
    subprocess.run(cmd)


def cleanup(args):
    f_path = Path(f"{args.sysname}-bootloader.elf.deleteme")
    if f_path.exists():
        f_path.unlink()

    f_path = Path(f"{args.sysname}-bl_image.bin.deleteme")
    if f_path.exists():
        f_path.unlink()

    log.info("Removed temporary files")


def get_args():
    parser = argparse.ArgumentParser(fromfile_prefix_chars="@")
    subparsers = parser.add_subparsers(dest="cmd", help="sub-command help")
    subparsers.required = True

    parser_kill = subparsers.add_parser("kill-system", help="kill-system help")
    parser_kill.add_argument("--sysname", required=True, help="SAFFIRe system name")
    parser_kill.set_defaults(func=kill_system)

    # Build SAFFIRe
    parser_create = subparsers.add_parser("build-system", help="build-system help")
    parser_create.add_argument(
        "--sysname",
        required=True,
        help="SAFFIRe system name",
    )
    parser_create.add_argument(
        "--oldest-allowed-version",
        required=True,
        help="Oldest allowed firmware version on device",
    )
    create_group = parser_create.add_mutually_exclusive_group(required=True)
    create_group.add_argument(
        "--physical",
        action="store_true",
        help="Run system for physical device",
    )
    create_group.add_argument(
        "--emulated",
        action="store_true",
        help="Run system for emulated device",
    )
    parser_create.set_defaults(func=build_system)

    # Load device with newest SAFFIRe bootloader
    parser_load = subparsers.add_parser("load-device", help="load-device help")
    parser_load.add_argument("--sysname", required=True, help="SAFFIRe system name")
    parser_load.add_argument(
        "--serial-port", default=None, help="Physical device serial port"
    )
    load_group = parser_load.add_mutually_exclusive_group(required=True)
    load_group.add_argument(
        "--physical",
        action="store_true",
        help="Run system for physical device",
    )
    load_group.add_argument(
        "--emulated",
        action="store_true",
        help="Run system for emulated device",
    )
    parser_load.set_defaults(func=load_device)

    # Run bootloader
    parser_bl = subparsers.add_parser(
        "launch-bootloader", help="launch-bootloader help"
    )
    parser_bl.add_argument("--sysname", required=True, help="SAFFIRe system name")
    parser_bl.add_argument("--sock-root", help="Directory to place sockets")
    parser_bl.add_argument("--uart-sock", required=True, help="UART interface socket")
    parser_bl.add_argument("--serial-port", help="Physical device serial port")
    bl_group = parser_bl.add_mutually_exclusive_group(required=True)
    bl_group.add_argument(
        "--physical",
        action="store_true",
        help="Run system for physical device",
    )
    bl_group.add_argument(
        "--emulated",
        action="store_true",
        help="Run system for emulated device",
    )
    parser_bl.set_defaults(func=launch_bootloader)

    # Run bootloader in interactive mode (emulated only)
    parser_bl_i = subparsers.add_parser(
        "launch-bootloader-interactive", help="launch-bootloader-interactive help"
    )
    parser_bl_i.add_argument("--sysname", required=True, help="SAFFIRe system name")
    parser_bl_i.add_argument(
        "--sock-root", required=True, help="Directory to place sockets"
    )
    parser_bl_i.add_argument("--uart-sock", required=True, help="UART interface socket")
    parser_bl_i.set_defaults(func=launch_bootloader_interactive)

    # Run bootloader with GDB (emulated only)
    parser_bl_gdb = subparsers.add_parser(
        "launch-bootloader-gdb", help="launch-bootloader-gdb help"
    )
    parser_bl_gdb.add_argument("--sysname", required=True, help="SAFFIRe system name")
    parser_bl_gdb.add_argument(
        "--sock-root", required=True, help="Directory to place sockets"
    )
    parser_bl_gdb.add_argument(
        "--uart-sock", required=True, help="UART interface socket"
    )
    parser_bl_gdb.set_defaults(func=launch_bootloader_gdb)

    # Firmware protect
    parser_fw_protect = subparsers.add_parser("fw-protect", help="fw-protect help")
    parser_fw_protect.add_argument(
        "--sysname", required=True, help="SAFFIRe system name"
    )
    parser_fw_protect.add_argument(
        "--fw-root", required=True, help="Directory to read and save firmware images"
    )
    parser_fw_protect.add_argument(
        "--raw-fw-file", required=True, help="Firmware protect input file"
    )
    parser_fw_protect.add_argument(
        "--protected-fw-file", required=True, help="Firmware protect output file"
    )
    parser_fw_protect.add_argument(
        "--fw-version", required=True, help="Firmware protect version"
    )
    parser_fw_protect.add_argument(
        "--fw-message", required=True, help="Firmware protect release message"
    )
    parser_fw_protect.set_defaults(func=fw_protect)

    # Configuration protect
    parser_cfg_protect = subparsers.add_parser("cfg-protect", help="cfg-protect help")
    parser_cfg_protect.add_argument(
        "--sysname", required=True, help="SAFFIRe system name"
    )
    parser_cfg_protect.add_argument(
        "--cfg-root",
        required=True,
        help="Directory to read and save configuration images",
    )
    parser_cfg_protect.add_argument(
        "--raw-cfg-file", required=True, help="Configuration protect input file"
    )
    parser_cfg_protect.add_argument(
        "--protected-cfg-file", required=True, help="Configuration protect output file"
    )
    parser_cfg_protect.set_defaults(func=cfg_protect)

    # Firmware update
    parser_fw_update = subparsers.add_parser("fw-update", help="fw-update help")
    parser_fw_update.add_argument(
        "--sysname", required=True, help="SAFFIRe system name"
    )
    parser_fw_update.add_argument(
        "--fw-root", required=True, help="Directory to read firmware images"
    )
    parser_fw_update.add_argument(
        "--uart-sock", required=True, help="UART interface socket"
    )
    parser_fw_update.add_argument(
        "--protected-fw-file", required=True, help="Firmware update input file"
    )
    parser_fw_update.set_defaults(func=fw_update)

    # Load configuration
    parser_cfg_load = subparsers.add_parser("cfg-load", help="cfg-load help")
    parser_cfg_load.add_argument("--sysname", required=True, help="SAFFIRe system name")
    parser_cfg_load.add_argument(
        "--cfg-root", required=True, help="Directory to read configuration images"
    )
    parser_cfg_load.add_argument(
        "--uart-sock", required=True, help="UART interface socket"
    )
    parser_cfg_load.add_argument(
        "--protected-cfg-file", required=True, help="Configuration load input file"
    )
    parser_cfg_load.set_defaults(func=cfg_load)

    # Firmware readback
    parser_fw_readback = subparsers.add_parser("fw-readback", help="fw-readback help")
    parser_fw_readback.add_argument(
        "--sysname", required=True, help="SAFFIRe system name"
    )
    parser_fw_readback.add_argument(
        "--uart-sock", required=True, help="UART interface socket"
    )
    parser_fw_readback.add_argument(
        "--rb-len", required=True, help="Readback request data length"
    )
    parser_fw_readback.set_defaults(func=fw_readback)

    # Configuration readback
    parser_cfg_readback = subparsers.add_parser(
        "cfg-readback", help="cfg-readback help"
    )
    parser_cfg_readback.add_argument(
        "--sysname", required=True, help="SAFFIRe system name"
    )
    parser_cfg_readback.add_argument(
        "--uart-sock", required=True, help="UART interface socket"
    )
    parser_cfg_readback.add_argument(
        "--rb-len", required=True, help="Readback request data length"
    )
    parser_cfg_readback.set_defaults(func=cfg_readback)

    # Device boot
    parser_boot = subparsers.add_parser("boot", help="boot help")
    parser_boot.add_argument("--sysname", required=True, help="SAFFIRe system name")
    parser_boot.add_argument("--uart-sock", required=True, help="UART interface socket")
    parser_boot.add_argument(
        "--boot-msg-file",
        required=True,
        help="File path for host to store booted release message in",
    )
    parser_boot.set_defaults(func=boot)

    # Firmware monitor
    parser_monitor = subparsers.add_parser("monitor", help="monitor help")
    parser_monitor.add_argument("--sysname", required=True, help="SAFFIRe system name")
    parser_monitor.add_argument(
        "--uart-sock", required=True, help="UART interface socket"
    )
    parser_monitor.add_argument(
        "--boot-msg-file",
        required=True,
        help="File path for host to read booted release messages from",
    )
    parser_monitor.set_defaults(func=monitor)

    # Clean up temporary files
    parser_cleanup = subparsers.add_parser("cleanup", help="cleanup help")
    parser_cleanup.add_argument("--sysname", required=True, help="SAFFIRe system name")
    parser_cleanup.set_defaults(func=cleanup)

    args, unknown = parser.parse_known_args()

    return args


def main():
    # Check that we are running from the root of the repo
    exec_dir = Path().resolve()
    expected_git_path = exec_dir / ".git"
    if not expected_git_path.exists():
        exit("ERROR: This script must be run from the root of the repo!")

    # Get args and call specified function
    args = get_args()
    args.func(args)


if __name__ == "__main__":
    main()
