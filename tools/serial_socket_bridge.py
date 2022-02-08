# 2022 eCTF
# Serial-Socket Bridge
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

import argparse
import logging
import socket
import select
import serial
from typing import Optional


class Port:
    def __init__(self, device_port: str, baudrate=115200, log_level=logging.INFO):
        self.device_port = device_port
        self.baudrate = baudrate
        self.ser = None

        # Set up logger
        self.logger = logging.getLogger(f"{device_port}_log")
        self.logger.info(f"Ready to connect to device on serial {self.device_port}")

    def active(self) -> bool:
        # If not connected, try to connect to serial device
        if not self.ser:
            try:
                ser = serial.Serial(
                    self.device_port, baudrate=self.baudrate, timeout=0.1
                )
                ser.reset_input_buffer()
                self.ser = ser
                self.logger.info(f"Connection opened on {self.device_port}")
            except (serial.SerialException, OSError):
                pass
        return bool(self.ser)

    def read_msg(self) -> Optional[bytes]:
        if not self.active():
            return None

        try:
            msg = self.ser.read()
            if msg != b"":
                return msg
            return None
        except (serial.SerialException, OSError):
            self.close()
            return None

    def send_msg(self, msg: bytes) -> bool:
        if not self.active():
            return False

        try:
            self.ser.write(msg)
            return True
        except (serial.SerialException, OSError):
            self.close()
            return False

    def close(self):
        self.logger.warning(f"Connection closed on {self.device_port}")
        self.ser = None


class Sock:
    def __init__(self, sock_port: int, q_len=1, log_level=logging.INFO):
        self.sock_port = sock_port

        # Set up socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", int(sock_port)))
        self.sock.listen(q_len)
        self.csock = None

        # Set up logger
        self.logger = logging.getLogger(f"{sock_port}_log")
        self.logger.info(f"Ready to connect to socket on port {self.sock_port}")

    @staticmethod
    def sock_ready(sock: socket.SocketType) -> bool:
        ready, _, _ = select.select([sock], [], [], 0)
        return bool(ready)

    def active(self) -> bool:
        # Try to accept new client
        if not self.csock:
            if self.sock_ready(self.sock):
                self.logger.info(f"Connection opened on {self.sock_port}")
                self.csock, _ = self.sock.accept()
        return bool(self.csock)

    def read_msg(self) -> Optional[bytes]:
        if not self.active():
            return None

        try:
            if self.sock_ready(self.csock):
                data = self.csock.recv(4096)

                # Connection closed
                if not data:
                    self.close()
                    return None

                return data
            return None
        except (ConnectionResetError, BrokenPipeError):
            # Cleanly handle forced closed connection
            self.close()
            return None

    def send_msg(self, msg: bytes) -> bool:
        if not self.active():
            return False

        try:
            self.csock.sendall(msg)
            return True
        except (ConnectionResetError, BrokenPipeError):
            # Cleanly handle forced closed connection
            self.close()
            return False

    def close(self):
        self.logger.warning(f"Conection closed on {self.sock_port}")
        self.csock = None


def poll_bridge(host_sock: Sock, device_port: Port):
    if host_sock.active():
        msg = host_sock.read_msg()

        # Send message to device
        if device_port.active():
            if msg is not None:
                device_port.send_msg(msg)

    if device_port.active():
        msg = device_port.read_msg()

        # Send message to host
        if host_sock.active():
            if msg is not None:
                host_sock.send_msg(msg)


def bridge(uart_sock: int, device_port: str):

    # Open all sockets
    uart_sock_obj = Sock(uart_sock)
    device_port_obj = Port(device_port)

    # poll socket to serial bridge forever
    while True:
        poll_bridge(uart_sock_obj, device_port_obj)


# Run in application mode
if __name__ == "__main__":

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")

    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--uart-sock",
        type=int,
        default=1337,
        help="Path to host-side data socket (will be created)",
    )
    parser.add_argument("--device-port", required=True, help="Device-side serial port")
    args = parser.parse_args()

    uart_sock, device_port = args.uart_sock, args.device_port

    bridge(uart_sock, device_port)
