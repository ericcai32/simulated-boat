"""Transport for local serial ports or a host-side TCP serial relay."""

import serial


class SerialPort:
    def __init__(self, port, baud_rate=9600):
        if not port:
            raise ValueError("Set teensy_port when dry_run is false")
        if baud_rate <= 0:
            raise ValueError("baud_rate must be positive")
        self.serial = serial.serial_for_url(
            port, baudrate=baud_rate, timeout=1.0, write_timeout=1.0
        )

    def send_packet(self, packet):
        if self.serial.write(packet) != len(packet):
            raise OSError("Incomplete serial write")

    def close(self):
        self.serial.close()
