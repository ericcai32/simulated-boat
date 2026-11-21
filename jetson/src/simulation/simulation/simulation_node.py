"""Scripted sensors and hardware feedback, without physical devices."""

import math
from collections import deque
from functools import partial

import rclpy
from geometry_msgs.msg import Vector3
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus
from std_msgs.msg import Int32, UInt8


class DelayedFeedback:
    def __init__(self, delay):
        self.delay = delay
        self.pending = deque()
        self.values = {
            "mainsail_angle": 0,
            "rudder_angle": 0,
            "jib_angle": 0,
            "jib_side_flag": 0,
        }

    def command(self, topic, value, now):
        self.pending.append((now + self.delay, topic, value))

    def sample(self, now):
        while self.pending and self.pending[0][0] <= now:
            _, topic, value = self.pending.popleft()
            self.values[topic] = value
        return self.values.copy()


def buoy_visible(elapsed_seconds):
    """Five seconds of detections followed by 25 seconds of silence."""
    return elapsed_seconds % 30.0 < 5.0


class Simulation(Node):
    def __init__(self):
        super().__init__("simulation")
        rate = float(self.declare_parameter("publish_rate", 10.0).value)
        delay = float(self.declare_parameter("feedback_delay", 0.3).value)
        if not math.isfinite(rate) or rate <= 0:
            raise ValueError("publish_rate must be positive and finite")
        if not math.isfinite(delay) or delay < 0:
            raise ValueError("feedback_delay must be nonnegative and finite")
        self.feedback = DelayedFeedback(delay)
        self.tick = 0
        self.started_at = self.get_clock().now().nanoseconds / 1e9
        self.gps = self.create_publisher(NavSatFix, "gps", 10)
        self.imu = self.create_publisher(Vector3, "imu", 10)
        self.wind = self.create_publisher(Int32, "wind_angle", 10)
        self.buoy = self.create_publisher(Vector3, "buoy_position", 10)
        self.feedback_publishers = {}
        for topic in self.feedback.values:
            msg_type = UInt8 if topic == "jib_side_flag" else Int32
            self.feedback_publishers[topic] = (
                self.create_publisher(msg_type, f"received_{topic}", 10),
                msg_type,
            )
            self.create_subscription(
                msg_type, topic, partial(self.command_callback, topic), 10
            )
        self.create_timer(1.0 / rate, self.publish_sample)

    def command_callback(self, topic, msg):
        self.feedback.command(topic, msg.data, self.get_clock().now().nanoseconds / 1e9)

    def publish_sample(self):
        phase = math.radians(self.tick % 360)
        gps = NavSatFix()
        gps.header.stamp = self.get_clock().now().to_msg()
        gps.header.frame_id = "gps"
        gps.status.status = NavSatStatus.STATUS_FIX
        gps.status.service = NavSatStatus.SERVICE_GPS
        gps.latitude = 42.45 + 0.0002 * math.sin(phase)
        gps.longitude = -76.51 + 0.0002 * math.cos(phase)
        self.gps.publish(gps)
        self.imu.publish(
            Vector3(
                x=5.0 * math.sin(phase),
                y=2.0 * math.cos(phase),
                z=float(self.tick % 360),
            )
        )
        self.wind.publish(Int32(data=self.tick % 360))
        # Camera axes: x right, y down, z forward; all distances in meters.
        elapsed = self.get_clock().now().nanoseconds / 1e9 - self.started_at
        if buoy_visible(elapsed):
            self.buoy.publish(
                Vector3(x=2.0 * math.sin(phase), y=0.5, z=10.0 + math.cos(phase))
            )
        values = self.feedback.sample(self.get_clock().now().nanoseconds / 1e9)
        for topic, (publisher, msg_type) in self.feedback_publishers.items():
            publisher.publish(msg_type(data=values[topic]))
        self.tick += 1


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = Simulation()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.try_shutdown()
