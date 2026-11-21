import socket
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest
from serial_relay import forward_client


def test_tcp_fragmentation_preserves_bytes():
    received = bytearray()
    port = Mock()

    def write(data):
        received.extend(data)
        return len(data)

    port.write.side_effect = write
    sender, receiver = socket.socketpair()
    sender.settimeout(2)
    receiver.settimeout(2)
    with sender, receiver, ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(forward_client, receiver, port)
        for fragment in [b"\xff", b"\x00\xee\xff\x01", b"\xee\xff\x02\xee\xff\x03\xee"]:
            sender.sendall(fragment)
        sender.shutdown(socket.SHUT_WR)
        future.result(timeout=3)
    assert received == b"\xff\x00\xee\xff\x01\xee\xff\x02\xee\xff\x03\xee"


def test_incomplete_write_is_reported():
    client = Mock()
    client.recv.return_value = b"\xff\x01\xee"
    port = Mock()
    port.write.return_value = 1
    with pytest.raises(OSError, match="Incomplete"):
        forward_client(client, port)


def test_serial_failure_propagates():
    client = Mock()
    client.recv.return_value = b"\xff\x01\xee"
    port = Mock()
    port.write.side_effect = OSError("disconnected")
    with pytest.raises(OSError, match="disconnected"):
        forward_client(client, port)
