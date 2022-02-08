# 2022 eCTF
# Bootloader Interface Emulator
# Ben Janis
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
import os
import logging
import socket
import select
from pathlib import Path
from typing import List, Optional, TypeVar

Message = TypeVar("Message")
LOG_FORMAT = "%(asctime)s:%(name)-s%(levelname)-8s %(message)s"


class Sock:
    def __init__(
        self,
        sock_path: str,
        q_len=1,
        log_level=logging.INFO,
        mode: int = None,
        network=False,
    ):
        self.sock_path = sock_path
        self.network = network
        self.buf = b""

        # set up socket
        if self.network:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(("0.0.0.0", int(sock_path)))
        else:
            # Make sure the socket does not already exist
            try:
                os.unlink(sock_path)
            except OSError:
                if os.path.exists(sock_path):
                    raise
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.bind(sock_path)

        self.sock.listen(q_len)
        self.csock = None

        # change permissions if necessary
        if mode and not self.network:
            os.chmod(sock_path, mode)

        # set up logger
        fhandler = logging.FileHandler("bl_interface.log")
        fhandler.setLevel(log_level)
        fhandler.setFormatter(logging.Formatter(LOG_FORMAT))

        shandler = logging.StreamHandler()
        shandler.setLevel(log_level)
        shandler.setFormatter(logging.Formatter(LOG_FORMAT))

        self.logger = logging.getLogger(f"{sock_path}_log")
        self.logger.addHandler(fhandler)
        self.logger.addHandler(shandler)
        self.logger.setLevel(log_level)

    @staticmethod
    def sock_ready(sock: socket.SocketType) -> bool:
        ready, _, _ = select.select([sock], [], [], 0)
        return bool(ready)

    def active(self) -> bool:
        # try to accept new client
        if not self.csock:
            if self.sock_ready(self.sock):
                self.logger.info(f"Connection opened on {self.sock_path}")
                self.csock, _ = self.sock.accept()
        return bool(self.csock)

    def deserialize(self) -> bytes:
        buf = self.buf
        self.buf = b""
        return buf

    def read_msg(self) -> Optional[Message]:
        if not self.active():
            return None

        try:
            if self.sock_ready(self.csock):
                data = self.csock.recv(4096)

                # connection closed
                if not data:
                    self.close()
                    return None

                self.buf += data

            return self.deserialize()
        except (ConnectionResetError, BrokenPipeError):
            # cleanly handle forced closed connection
            self.close()
            return None

    def read_all_msgs(self) -> List[Message]:
        msgs = []
        msg = self.read_msg()
        while msg:
            msgs.append(msg)
            msg = self.read_msg()
        return msgs

    @staticmethod
    def serialize(msg: bytes) -> bytes:
        return msg

    def send_msg(self, msg: Message) -> bool:
        if not self.active():
            return False

        try:
            self.csock.sendall(self.serialize(msg))
            return True
        except (ConnectionResetError, BrokenPipeError):
            # cleanly handle forced closed connection
            self.close()
            return False

    def close(self):
        self.logger.warning(f"Conection closed on {self.sock_path}")
        self.csock = None
        self.buf = b""


def poll_data_socks(device_sock: Sock, host_sock: Sock):
    if device_sock.active():
        msg = device_sock.read_msg()

        # send message to host
        if host_sock.active():
            if msg is not None:
                host_sock.send_msg(msg)

    if host_sock.active():
        msg = host_sock.read_msg()

        # send message to device
        if device_sock.active():
            if msg is not None:
                device_sock.send_msg(msg)


def poll_restart_socks(device_sock: Sock, host_sock: Sock):
    # First check that device opened a restart port
    if device_sock.active():
        # Send host restart commands to device
        if host_sock.active():
            msg = host_sock.read_msg()
            if msg is not None:
                device_sock.send_msg(msg)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-bl-sock",
        type=Path,
        required=True,
        help="Path to device-side data socket (will be created)",
    )
    parser.add_argument(
        "--data-host-sock",
        type=int,
        required=True,
        help="Port for host-side data socket (must be available)",
    )
    parser.add_argument(
        "--restart-bl-sock",
        type=Path,
        required=True,
        help="Path to device-side data socket (will be created)",
    )
    parser.add_argument(
        "--restart-host-sock",
        type=Path,
        required=True,
        help="Path to device-side data socket (will be created)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # open all sockets
    data_bl = Sock(str(args.data_bl_sock), mode=0o777)
    data_host = Sock(str(args.data_host_sock), mode=0o777, network=True)

    restart_bl = Sock(str(args.restart_bl_sock), mode=0o777)
    restart_host = Sock(str(args.restart_host_sock), mode=0o777)

    # poll sockets forever
    while True:
        poll_data_socks(data_bl, data_host)
        poll_restart_socks(restart_bl, restart_host)


if __name__ == "__main__":
    main()
