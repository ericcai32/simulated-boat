from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import rclpy
from sailing.reinforcement_learning.reinforcement_learning_node import scripted_commands
from sailing.teensy.serial_port import SerialPort
from sailing.teensy.teensy_node import Teensy, encode_no_go_band
from std_msgs.msg import UInt8


@pytest.mark.parametrize("band", range(4))
def test_packet(band):
    assert encode_no_go_band(UInt8(data=band)) == bytes([255, band, 238])


@pytest.mark.parametrize("band", [-1, 4, 255])
def test_invalid_packet(band):
    with pytest.raises(ValueError):
        encode_no_go_band(SimpleNamespace(data=band))


def test_scripted_commands_cover_ranges_and_repeat():
    samples = [scripted_commands(i) for i in range(360)]
    for column, expected in enumerate(
        [set(range(91)), set(range(-45, 46)), set(range(91)), {0, 1}]
    ):
        assert {sample[column] for sample in samples} == expected
    assert scripted_commands(0) == scripted_commands(360)


def test_transport_writes_and_closes(monkeypatch):
    connection = Mock()
    connection.write.return_value = 3
    factory = Mock(return_value=connection)
    monkeypatch.setattr("sailing.teensy.serial_port.serial.serial_for_url", factory)
    transport = SerialPort("socket://localhost:7000")
    factory.assert_called_once_with(
        "socket://localhost:7000", baudrate=9600, timeout=1.0, write_timeout=1.0
    )
    transport.send_packet(b"\xff\x02\xee")
    connection.write.assert_called_once_with(b"\xff\x02\xee")
    connection.write.return_value = 1
    with pytest.raises(OSError, match="Incomplete"):
        transport.send_packet(b"\xff\x02\xee")
    connection.write.side_effect = OSError("disconnected")
    with pytest.raises(OSError, match="disconnected"):
        transport.send_packet(b"\xff\x02\xee")
    transport.close()
    connection.close.assert_called_once()


def test_empty_port_rejected():
    with pytest.raises(ValueError, match="teensy_port"):
        SerialPort("")


def test_node_write_failure_closes_transport(monkeypatch):
    transport = Mock()
    transport.send_packet.side_effect = OSError("disconnected")
    monkeypatch.setattr(
        "sailing.teensy.teensy_node.SerialPort", Mock(return_value=transport)
    )
    rclpy.init(args=["--ros-args", "-p", "dry_run:=false", "-p", "teensy_port:=test"])
    node = Teensy()
    try:
        with pytest.raises(OSError, match="disconnected"):
            node.no_go_band_callback(UInt8(data=2))
    finally:
        node.destroy_node()
        rclpy.shutdown()
    transport.close.assert_called_once()


def test_dry_run_never_opens_serial(monkeypatch, capfd):
    factory = Mock(side_effect=AssertionError("dry run must not open USB"))
    monkeypatch.setattr("sailing.teensy.teensy_node.SerialPort", factory)
    rclpy.init(args=[])
    node = Teensy()
    try:
        node.no_go_band_callback(UInt8(data=3))
    finally:
        node.destroy_node()
        rclpy.shutdown()
    factory.assert_not_called()
    captured = capfd.readouterr()
    assert "ff 03 ee" in captured.err + captured.out


def test_connection_failure_is_visible(monkeypatch):
    factory = Mock(side_effect=OSError("port unavailable"))
    monkeypatch.setattr("sailing.teensy.serial_port.serial.serial_for_url", factory)
    with pytest.raises(OSError, match="port unavailable"):
        SerialPort("missing")
