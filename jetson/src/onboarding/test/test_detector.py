import pytest
from onboarding.no_go_band_node import no_go_zone_band


@pytest.mark.parametrize(
    "angle,expected",
    [
        (0, 0),
        (44, 0),
        (45, 0),
        (46, 1),
        (89, 1),
        (90, 1),
        (91, 2),
        (134, 2),
        (135, 2),
        (136, 3),
        (180, 3),
        (224, 3),
        (225, 2),
        (269, 2),
        (270, 1),
        (314, 1),
        (315, 0),
        (359, 0),
        (360, 0),
        (-45, 0),
        (-46, 1),
        (450, 1),
        (720, 0),
    ],
)
def test_bands(angle, expected):
    assert no_go_zone_band(angle) == expected
