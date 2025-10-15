import pytest
import time

from birdbrain_constant import BirdbrainConstant
from birdbrain_exception import BirdbrainException
from birdbrain_hummingbird_input import BirdbrainHummingbirdInput

def test_acceleration():
    response = BirdbrainHummingbirdInput.acceleration("A")

    assert (-100.0 <= response[0] <= 100.0)
    assert (-100.0 <= response[1] <= 100.0)
    assert (-100.0 <= response[2] <= 100.0)

    assert isinstance(response[0], float)
    assert isinstance(response[1], float)
    assert isinstance(response[2], float)

def test_compass():
    response = BirdbrainHummingbirdInput.compass("A")

    assert (0 <= response <= 359)
    assert isinstance(response, int)

def test_magnetometer():
    response = BirdbrainHummingbirdInput.magnetometer("A")

    assert (-180.0 <= response[0] <= 180.0)
    assert (-180.0 <= response[1] <= 180.0)
    assert (-180.0 <= response[2] <= 180.0)

    assert isinstance(response[0], int)
    assert isinstance(response[1], int)
    assert isinstance(response[2], int)

def test_orientation():
    response = BirdbrainHummingbirdInput.orientation("A")

    some_position = False
    for orientation in BirdbrainConstant.HUMMINGBIRD_ORIENTATION_RESULTS:
        some_position = some_position or (orientation == response)

    assert some_position

def test_sensor():
    response = BirdbrainHummingbirdInput.sensor("A", 1)

    assert isinstance(response, float)

def test_light():
    response = BirdbrainHummingbirdInput.light("A", 1)
    assert (0 <= response <= 100)
    assert isinstance(response, int)

def test_sound():
    response = BirdbrainHummingbirdInput.sound("A", 1)
    assert (0 <= response <= 100)
    assert isinstance(response, int)

    with pytest.raises(BirdbrainException) as e:
        response = BirdbrainHummingbirdInput.sound("A", 4)
    assert e.value.message == "Error: The device is not connected"

def test_sound_microbit():
    response = BirdbrainHummingbirdInput.sound("A", "micro:bit")

    assert (0 <= response <= 100)
    assert isinstance(response, int)

def test_distance():
    response = BirdbrainHummingbirdInput.distance("A", 2)

    assert (0 <= response <= 298)
    assert isinstance(response, int)

def test_dial():
    response = BirdbrainHummingbirdInput.dial("A", 1)

    assert (0 <= response <= 100)
    assert isinstance(response, int)

def test_voltage():
    response = BirdbrainHummingbirdInput.voltage("A", 1)

    assert (0.0 <= response <= 3.3)
    assert isinstance(response, float)
