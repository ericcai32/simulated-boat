"""Run on the Mac/Windows host to forward container TCP output to USB serial."""

import argparse
import socket

import serial


def forward_client(client, port):
    """TCP chunks need not align with packets; forward every byte in order."""
    while True:
        data = client.recv(4096)
        if not data:
            return
        if port.write(data) != len(data):
            raise OSError("Incomplete serial write")


def serve(port, host, tcp_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, tcp_port))
        server.listen(1)
        print(f"Listening on {host}:{tcp_port}; Ctrl-C to stop", flush=True)
        # Handle one connection at a time. A disconnected client can reconnect.
        while True:
            client, address = server.accept()
            print(f"Connected: {address}", flush=True)
            with client:
                try:
                    forward_client(client, port)
                except ConnectionError as exc:
                    print(f"Client disconnected: {exc}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--port", required=True, help="e.g. COM3 or /dev/cu.usbmodem123"
    )
    parser.add_argument("--baud-rate", type=int, default=9600)
    parser.add_argument(
        "--host", default="0.0.0.0", help="Interface accessible to Docker Desktop"
    )
    parser.add_argument("--tcp-port", type=int, default=7000)
    args = parser.parse_args()
    try:
        with serial.Serial(
            args.port, baudrate=args.baud_rate, timeout=1, write_timeout=1
        ) as port:
            serve(port, args.host, args.tcp_port)
    except KeyboardInterrupt:
        pass
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Serial relay failed: {exc}\n")


if __name__ == "__main__":
    main()
