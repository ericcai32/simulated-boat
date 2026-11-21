"""Completed no-go-band example."""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Int32, UInt8


def no_go_zone_band(angle):
    angle %= 360
    distance = min(angle, 360 - angle)
    if distance <= 45:
        return 0
    if distance <= 90:
        return 1
    if distance <= 135:
        return 2
    return 3


class NoGoBand(Node):
    def __init__(self):
        super().__init__("no_go_band")
        self.publisher = self.create_publisher(UInt8, "no_go_zone_band", 10)
        self.create_subscription(Int32, "wind_angle", self.wind_callback, 10)

    def wind_callback(self, msg):
        self.publisher.publish(UInt8(data=no_go_zone_band(msg.data)))


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = NoGoBand()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.try_shutdown()
