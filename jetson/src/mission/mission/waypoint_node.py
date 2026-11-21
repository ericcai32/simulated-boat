"""Repeatable target for onboarding subscribers."""

import math
from collections import deque

import rclpy
from interface.msg import Waypoint
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus

# Targets lie on the simulated GPS loop, in its direction of travel.
ROUTE = (
    ("north", 42.4502, -76.51),
    ("west", 42.45, -76.5102),
    ("south", 42.4498, -76.51),
    ("east", 42.45, -76.5098),
)


def distance_m(latitude, longitude, target_latitude, target_longitude):
    lat1, lat2 = math.radians(latitude), math.radians(target_latitude)
    dlat = lat2 - lat1
    dlon = math.radians(target_longitude - longitude)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 6371000.0 * 2 * math.asin(math.sqrt(min(1.0, max(0.0, a))))


class WaypointQueue:
    def __init__(self, arrival_radius=3.0):
        self.arrival_radius = arrival_radius
        self.pending = deque(ROUTE)

    def update(self, latitude, longitude):
        _, target_latitude, target_longitude = self.pending[0]
        if (
            distance_m(latitude, longitude, target_latitude, target_longitude)
            > self.arrival_radius
        ):
            return False
        self.pending.popleft()
        if not self.pending:
            self.pending.extend(ROUTE)
        return True


class WaypointPublisher(Node):
    def __init__(self):
        super().__init__("waypoint")
        rate = float(self.declare_parameter("publish_rate", 10.0).value)
        radius = float(self.declare_parameter("arrival_radius", 3.0).value)
        if not math.isfinite(rate) or rate <= 0:
            raise ValueError("publish_rate must be positive and finite")
        if not math.isfinite(radius) or radius <= 0:
            raise ValueError("arrival_radius must be positive and finite")
        self.waypoints = WaypointQueue(radius)
        self.publisher = self.create_publisher(Waypoint, "current_waypoint", 10)
        self.create_subscription(NavSatFix, "gps", self.gps_callback, 10)
        self.create_timer(1.0 / rate, self.publish_waypoint)

    def gps_callback(self, msg):
        if (
            msg.status.status == NavSatStatus.STATUS_NO_FIX
            or not math.isfinite(msg.latitude)
            or not math.isfinite(msg.longitude)
            or not -90 <= msg.latitude <= 90
            or not -180 <= msg.longitude <= 180
        ):
            return
        if self.waypoints.update(msg.latitude, msg.longitude):
            self.publish_waypoint()

    def publish_waypoint(self):
        waypoint_id, latitude, longitude = self.waypoints.pending[0]
        self.publisher.publish(
            Waypoint(id=waypoint_id, latitude=latitude, longitude=longitude)
        )


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = WaypointPublisher()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.try_shutdown()
