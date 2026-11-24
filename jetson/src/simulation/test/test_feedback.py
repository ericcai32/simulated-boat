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


def test_heel_capsize_and_recovery_repeat():
    from simulation.simulation_node import scripted_roll

    for cycle in (0, 60, 120):
        for time in (0, 9.999, 34, 39, 52, 59.999):
            assert abs(scripted_roll(cycle + time, 1.0)) <= 5
        for time in (10, 17.999):
            assert scripted_roll(cycle + time, 1.0) == 35
        for time in (18, 25.999):
            assert scripted_roll(cycle + time, 1.0) == -35
        for time in (26, 33.999):
            assert scripted_roll(cycle + time, 1.0) == 170


def test_stuck_feedback_holds_angles_and_recovers_latest_commands():
    from simulation.simulation_node import actuators_stuck

    feedback = DelayedFeedback(0.3)
    for topic, value in [
        ("mainsail_angle", 10),
        ("rudder_angle", -20),
        ("jib_angle", 30),
    ]:
        feedback.command(topic, value, 39)
    baseline = feedback.sample(39.5)
    for now in range(40, 52):
        feedback.command("mainsail_angle", now, now - 0.5)
        feedback.command("rudder_angle", now - 45, now - 0.5)
        feedback.command("jib_angle", 90 - now, now - 0.5)
        feedback.command("jib_side_flag", now % 2, now - 0.5)
        values = feedback.sample(now, stuck=actuators_stuck(now))
        for topic in ("mainsail_angle", "rudder_angle", "jib_angle"):
            assert values[topic] == baseline[topic]
        assert values["jib_side_flag"] == now % 2
        assert not feedback.pending
    assert feedback.sample(52, stuck=actuators_stuck(52)) == {
        "mainsail_angle": 51,
        "rudder_angle": 6,
        "jib_angle": 39,
        "jib_side_flag": 1,
    }
    assert not actuators_stuck(39.999)
    assert actuators_stuck(40)
    assert actuators_stuck(51.999)
    assert not actuators_stuck(52)
    assert actuators_stuck(100)
