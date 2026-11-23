"""Send your onboarding node's output to your Teensy."""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import UInt8

from .serial_port import SerialPort


def encode_no_go_band(msg):
    # Completed no-go-zone example encoder.
    # Example: start marker, one unsigned 8-bit band, end marker.
    if not 0 <= msg.data <= 3:
        raise ValueError("no_go_zone_band must be between 0 and 3")
    return bytes([0xFF, msg.data, 0xEE])


def encode_chloe_output(msg):
    # TODO: convert your project's output to packet bytes.
    ...


def encode_matteus_output(msg):
    # TODO: convert your project's output to packet bytes.
    ...


def encode_yul_output(msg):
    # TODO: convert your project's output to packet bytes.
    ...


def encode_dylan_output(msg):
    # TODO: convert your project's output to packet bytes.
    ...


class Teensy(Node):
    def __init__(self):
        super().__init__("teensy")
        self.serial_port = None
        try:
            self.dry_run = self.declare_parameter("dry_run", True).value
            port = self.declare_parameter("teensy_port", "").value
            baud = self.declare_parameter("baud_rate", 9600).value
            if not self.dry_run:
                self.serial_port = SerialPort(port, baud)
            self.project = self.declare_parameter("project", "no_go_band").value
            if self.project not in ("no_go_band", "chloe", "matteus", "yul", "dylan"):
                raise ValueError(f"Unknown project: {self.project}")
            if self.project == "no_go_band":
                self.create_subscription(
                    UInt8, "no_go_zone_band", self.no_go_band_callback, 10
                )
            if self.project == "dylan":
                self.create_subscription(Bool, "flipped_override", self.dylan_callback, 10)
            else:
                # TODO: add your project's subscription here, guarded by its name.
                # Choose your own topic/type and use your matching encoder.
                self.get_logger().info(
                    f"{self.project}: subscription not implemented yet"
                )
            self.get_logger().info(
                "Printing packets" if self.dry_run else f"Connected to {port}"
            )
        except Exception as exc:
            self.get_logger().error(f"Teensy setup failed: {exc}")
            self.destroy_node()
            raise

    def no_go_band_callback(self, msg):
        self.encode_and_send(msg, encode_no_go_band)

    def dylan_callback(self, msg):
        self.encode_and_send(msg, encode_dylan_output)

    def encode_and_send(self, msg, encoder):
        try:
            packet = encoder(msg)
        except ValueError as exc:
            self.get_logger().warning(f"Invalid project output: {exc}")
            return
        if packet is None:
            return
        if self.dry_run:
            self.get_logger().info(f"TX {packet.hex(' ')}")
        else:
            try:
                self.serial_port.send_packet(packet)
            except OSError as exc:
                self.get_logger().error(
                    f"Serial write failed: {exc}; restart after reconnecting"
                )
                raise

    def destroy_node(self):
        try:
            if self.serial_port is not None:
                self.serial_port.close()
                self.serial_port = None
        finally:
            result = super().destroy_node()
        return result


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = Teensy()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.try_shutdown()
