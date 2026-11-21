"""Scripted stand-in for boat's RL node; no model or physics is involved."""

import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Int32, UInt8


def scripted_commands(tick):
    position = tick % 180
    sail = position if position <= 90 else 180 - position
    return sail, sail - 45, 90 - sail, (tick // 90) % 2


class ReinforcementLearning(Node):
    def __init__(self):
        super().__init__("reinforcement_learning")
        rate = float(self.declare_parameter("publish_rate", 10.0).value)
        if not math.isfinite(rate) or rate <= 0:
            raise ValueError("publish_rate must be positive and finite")
        self.tick = 0
        self.publishers_by_topic = [
            (self.create_publisher(msg_type, topic, 10), msg_type)
            for topic, msg_type in [
                ("mainsail_angle", Int32),
                ("rudder_angle", Int32),
                ("jib_angle", Int32),
                ("jib_side_flag", UInt8),
            ]
        ]
        self.create_timer(1.0 / rate, self.publish_commands)

    def publish_commands(self):
        for (publisher, msg_type), value in zip(
            self.publishers_by_topic, scripted_commands(self.tick)
        ):
            publisher.publish(msg_type(data=value))
        self.tick += 1


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = ReinforcementLearning()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.try_shutdown()
