"""Chloe's project. Use no_go_band_node.py as a reference."""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class ChloeNode(Node):
    def __init__(self):
        super().__init__("chloe_node")
        # TODO: add your publishers, subscriptions, and project logic.
        ...


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = ChloeNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.try_shutdown()
