import math

from mission.waypoint_node import ROUTE, WaypointQueue, distance_m


def test_distant_gps_does_not_pop_target():
    queue = WaypointQueue()
    for _ in range(100):
        assert not queue.update(42.45, -76.5098)
    assert tuple(queue.pending) == ROUTE


def test_targets_pop_in_order_and_route_restarts():
    queue = WaypointQueue()
    for target in ROUTE:
        assert queue.pending[0] == target
        assert queue.update(target[1], target[2])
    assert tuple(queue.pending) == ROUTE


def test_simulated_gps_reaches_each_target_in_order():
    queue = WaypointQueue()
    reached = []
    for tick in range(360):
        phase = math.radians(tick)
        target = queue.pending[0]
        if queue.update(
            42.45 + 0.0002 * math.sin(phase), -76.51 + 0.0002 * math.cos(phase)
        ):
            reached.append(target[0])
    assert reached == [target[0] for target in ROUTE]


def test_arrival_radius_in_meters():
    queue = WaypointQueue(3.0)
    _, latitude, longitude = ROUTE[0]
    assert 2 < distance_m(latitude + 0.00002, longitude, latitude, longitude) < 3
    assert not queue.update(latitude + 0.00004, longitude)
    assert queue.update(latitude + 0.00002, longitude)
