#!/usr/bin/python3 -u

# 2022 eCTF
# Example side-channel collector
# Jake Grycel, Mark Clark, Dallas Phillips
#
# (c) 2022 The MITRE Corporation
#
# This source file is part of an example system for MITRE's 2022 Embedded System
# CTF (eCTF). This code is being provided only for educational purposes for the
# 2022 MITRE eCTF competition, and may not meet MITRE standards for quality.
# Use this code at your own risk!
#
# DO NOT CHANGE THIS FILE

import threading
import argparse
import socket
import time
import os


def parse_args():
    parser = argparse.ArgumentParser(description="Basic Side-Channel Receiver")

    parser.add_argument(
        "--uart-sock",
        type=int,
        help="Socket port that connects to the bootloader UART",
        required=True,
    )
    parser.add_argument(
        "--sc-sock", help="Path to the side channel socket", required=True
    )
    parser.add_argument(
        "--i-file", help="Name of the file to load 16 bytes of data from", required=True
    )
    parser.add_argument(
        "--o-file", help="Name of the file to print sc data to", required=True
    )
    parser.add_argument(
        "--byte-skip-count",
        default=-1,
        type=int,
        help="Number of bytes to skip from the input file",
        required=True,
    )
    parser.add_argument(
        "--num-samples",
        default=-1,
        type=int,
        help="Maximum number of samples per trace",
        required=True,
    )
    return parser.parse_args()


# Continuously collect side-channel traces
# Save data when told to by the main thread
def read_sc_data(sc_sock, o_file, start, stop, num_samples):
    # Connect side-channel probe socket
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(sc_sock)
        samples_temp = num_samples
        with open(o_file, "wb") as out_file:
            # Continuosuly read data
            while True:
                data = sock.recv(1024)

                # Only save data if the "start" event has been set
                if start.isSet() and samples_temp > 0:
                    if samples_temp < len(data):
                        out_file.write(data[:samples_temp])
                        samples_temp = 0
                    else:
                        out_file.write(data)
                        samples_temp -= len(data)

                if stop.isSet():
                    return


# Function to skip `byte_skip_count` bytes and then read and return 16 bytes
def read_input_data(i_file, byte_skip_count):
    with open(i_file, "rb") as in_file:
        if byte_skip_count > 0:
            in_file.read(byte_skip_count)
        return in_file.read(16)


# function to append bytes to a file
def write_output_data(o_file, data):
    with open(o_file, "ab") as out_file:
        out_file.write(data)


# Main function
def main():
    args = parse_args()

    uart_sock = args.uart_sock
    sc_sock = os.path.abspath(args.sc_sock)
    num_samples = args.num_samples
    byte_skip_count = args.byte_skip_count

    start = threading.Event()
    stop = threading.Event()

    # Start side-channel collector thread
    sc_thread = threading.Thread(
        target=read_sc_data,
        args=(
            sc_sock,
            args.o_file,
            start,
            stop,
            num_samples,
        ),
    )
    sc_thread.start()

    # Open UART data socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("0.0.0.0", uart_sock))

        # Read plaintext bytes from file
        print("\nGetting plaintext...")
        text = read_input_data(args.i_file, byte_skip_count)

        # Send to bootloader and tell collector thread to start saving samples
        print("Collecting traces...")
        start.set()
        sock.send(text)

        # Wait for response
        print("Finishing")
        time.sleep(0.1)
        data = sock.recv(1)

        if data[0] != 0x6:
            print("Error. Bootloader did not respond with 0x6")

        # Tell collector thread to stop saving samples
        stop.set()


if __name__ == "__main__":
    main()
