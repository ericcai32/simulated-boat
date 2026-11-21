from simulation.simulation_node import DelayedFeedback


def test_feedback_waits_and_preserves_command_order():
    feedback = DelayedFeedback(0.3)
    feedback.command("rudder_angle", -45, 1.0)
    feedback.command("rudder_angle", 45, 1.1)
    feedback.command("jib_side_flag", 1, 1.1)
    assert feedback.sample(1.29)["rudder_angle"] == 0
    assert feedback.sample(1.3)["rudder_angle"] == -45
    assert feedback.sample(1.41)["rudder_angle"] == 45
    assert feedback.sample(1.41)["jib_side_flag"] == 1
    assert not feedback.pending


def test_buoy_detection_windows():
    from simulation.simulation_node import buoy_visible

    assert buoy_visible(0)
    assert buoy_visible(4.999)
    assert not buoy_visible(5)
    assert not buoy_visible(15)
    assert not buoy_visible(29.999)
    assert buoy_visible(30)
    assert buoy_visible(34.999)
    assert not buoy_visible(35)
