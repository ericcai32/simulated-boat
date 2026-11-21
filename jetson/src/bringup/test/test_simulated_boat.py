"""Launch the actual graph and capture the Teensy bridge's TCP packets."""

import os
import signal
import socket
import subprocess
import tempfile
import threading
import time

import rclpy
from geometry_msgs.msg import Vector3
from interface.msg import Waypoint
from rclpy.executors import SingleThreadedExecutor
from sensor_msgs.msg import NavSatFix
from std_msgs.msg import Int32, UInt8


def test_full_graph(monkeypatch):
    monkeypatch.setenv("ROS_LOCALHOST_ONLY", "1")
    topics = {
        "gps": NavSatFix,
        "imu": Vector3,
        "wind_angle": Int32,
        "current_waypoint": Waypoint,
        "buoy_position": Vector3,
        "mainsail_angle": Int32,
        "rudder_angle": Int32,
        "jib_angle": Int32,
        "jib_side_flag": UInt8,
        "received_mainsail_angle": Int32,
        "received_rudder_angle": Int32,
        "received_jib_angle": Int32,
        "received_jib_side_flag": UInt8,
        "no_go_zone_band": UInt8,
    }
    samples = {topic: [] for topic in topics}
    buoy_times = []
    waypoint_ids = []

    def record(topic, msg):
        samples[topic].append(msg)
        if topic == "buoy_position":
            buoy_times.append(time.monotonic())
        elif topic == "current_waypoint":
            if not waypoint_ids or waypoint_ids[-1] != msg.id:
                waypoint_ids.append(msg.id)

    wire = bytearray()
    stop = threading.Event()
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    server.settimeout(0.2)

    def capture():
        while not stop.is_set():
            try:
                connection, _ = server.accept()
                break
            except socket.timeout:
                continue
        else:
            return
        with connection:
            connection.settimeout(0.2)
            while not stop.is_set():
                try:
                    data = connection.recv(4096)
                except socket.timeout:
                    continue
                if not data:
                    break
                wire.extend(data)

    thread = threading.Thread(target=capture)
    thread.start()
    context = rclpy.context.Context()
    domain = 50 + os.getpid() % 100
    rclpy.init(context=context, domain_id=domain)
    observer = rclpy.create_node("test_observer", context=context)
    executor = SingleThreadedExecutor(context=context)
    executor.add_node(observer)
    subscriptions = [
        observer.create_subscription(
            msg_type, topic, lambda msg, name=topic: record(name, msg), 100
        )
        for topic, msg_type in topics.items()
    ]
    process = None
    with tempfile.TemporaryFile(mode="w+") as log:
        try:
            environment = dict(
                os.environ, ROS_DOMAIN_ID=str(domain), ROS_LOCALHOST_ONLY="1"
            )
            process = subprocess.Popen(
                [
                    "ros2",
                    "launch",
                    "bringup",
                    "simulated_boat.launch.py",
                    "publish_rate:=120.0",
                    "dry_run:=false",
                    f"teensy_port:=socket://127.0.0.1:{server.getsockname()[1]}",
                ],
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            deadline = time.monotonic() + 38
            while time.monotonic() < deadline:
                executor.spin_once(timeout_sec=0.02)
                if process.poll() is not None:
                    break
                if (
                    all(len(values) >= 20 for values in samples.values())
                    and {m.data for m in samples["no_go_zone_band"]} == {0, 1, 2, 3}
                    and len(wire) >= 30
                    and any(b - a > 24 for a, b in zip(buoy_times, buoy_times[1:]))
                    and len(waypoint_ids) >= 5
                ):
                    # Continue a full cycle after discovery so serial covers all bands too.
                    if {wire[i] for i in range(1, len(wire) - 1, 3)} == {0, 1, 2, 3}:
                        break
            log.seek(0)
            output = log.read()
            assert process.poll() is None, output
            assert all(samples.values()), (
                [(k, len(v)) for k, v in samples.items()],
                output,
            )
            for topic, messages in samples.items():
                if topic == "gps" or topic == "current_waypoint":
                    assert all(
                        -90 <= m.latitude <= 90 and -180 <= m.longitude <= 180
                        for m in messages
                    )
                elif topic == "imu":
                    assert all(
                        -5 <= m.x <= 5 and -2 <= m.y <= 2 and 0 <= m.z < 360
                        for m in messages
                    )
                elif topic == "buoy_position":
                    assert all(
                        -2 <= m.x <= 2 and m.y == 0.5 and 9 <= m.z <= 11
                        for m in messages
                    )
                else:
                    low, high = (0, 90)
                    if "rudder" in topic:
                        low, high = -45, 45
                    elif "side_flag" in topic:
                        low, high = 0, 1
                    elif topic == "wind_angle":
                        low, high = 0, 359
                    elif topic == "no_go_zone_band":
                        low, high = 0, 3
                    assert all(low <= m.data <= high for m in messages), topic
            assert {m.data for m in samples["no_go_zone_band"]} == {0, 1, 2, 3}
            for name in [
                "mainsail_angle",
                "rudder_angle",
                "jib_angle",
                "jib_side_flag",
            ]:
                assert len({m.data for m in samples[f"received_{name}"]}) > 1
            assert any(24 < b - a < 28 for a, b in zip(buoy_times, buoy_times[1:]))
            assert set(waypoint_ids) == {"north", "west", "south", "east"}
            next_target = {
                "north": "west",
                "west": "south",
                "south": "east",
                "east": "north",
            }
            assert all(
                next_target[a] == b for a, b in zip(waypoint_ids, waypoint_ids[1:])
            )
            complete = bytes(wire[: len(wire) // 3 * 3])
            assert complete
            assert set(complete[0::3]) == {0xFF}
            assert set(complete[2::3]) == {0xEE}
            assert set(complete[1::3]) == {0, 1, 2, 3}
        finally:
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGINT)
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=3)
            for subscription in subscriptions:
                observer.destroy_subscription(subscription)
            executor.shutdown()
            observer.destroy_node()
            context.shutdown()
            stop.set()
            thread.join(timeout=3)
            server.close()


def test_member_launches_select_only_requested_project():
    for project in ("chloe", "matteus", "yul", "dylan"):
        with tempfile.TemporaryFile(mode="w+") as log:
            process = subprocess.Popen(
                [
                    "ros2",
                    "launch",
                    "bringup",
                    "simulated_boat.launch.py",
                    f"project:={project}",
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                deadline = time.monotonic() + 5
                output = ""
                while time.monotonic() < deadline:
                    log.seek(0)
                    output = log.read()
                    if "subscription not implemented yet" in output:
                        break
                    time.sleep(0.05)
                # The selected member must keep spinning instead of returning from main.
                time.sleep(0.5)
                log.seek(0)
                output = log.read()
                assert process.poll() is None, output
                assert f"[{project}_node-" in output, output
                assert "process has finished" not in output, output
                assert "process has died" not in output, output
                assert f"{project}: subscription not implemented yet" in output, output
                for node in (
                    "simulation_node",
                    "waypoint_node",
                    "reinforcement_learning_node",
                    "teensy_node",
                ):
                    assert f"[{node}-" in output, output
                for other in {"no_go_band", "chloe", "matteus", "yul", "dylan"} - {
                    project
                }:
                    assert f"[{other}_node-" not in output, output
                assert "TX " not in output, output
                assert "[ERROR]" not in output, output
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGINT)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=3)
