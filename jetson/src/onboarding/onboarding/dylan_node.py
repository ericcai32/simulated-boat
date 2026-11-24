"""Dylan's project. Use no_go_band_node.py as a reference."""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from geometry_msgs.msg import Vector3
from std_msgs.msg import Bool


class DylanNode(Node):
    def __init__(self):
        super().__init__("dylan_node")
        self.publisher = self.create_publisher(Bool, "flipped_override", 10)
        self.create_subscription(Vector3, "imu", self.flipped_over_callback, 10)

    def flipped_over_callback(self, msg):
        self.publisher.publish(Bool(data=abs(msg.x) >= 90.0))


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = DylanNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.try_shutdown()
