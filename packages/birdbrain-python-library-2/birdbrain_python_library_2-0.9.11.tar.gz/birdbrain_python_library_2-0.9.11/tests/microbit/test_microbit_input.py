import pytest

from birdbrain_constant import BirdbrainConstant
from birdbrain_exception import BirdbrainException
from birdbrain_microbit_input import BirdbrainMicrobitInput

def test_acceleration():
    response = BirdbrainMicrobitInput.acceleration("A", "Accelerometer")
    response = BirdbrainMicrobitInput.acceleration("A")

    assert (-100.0 <= response[0] <= 100.0)
    assert (-100.0 <= response[1] <= 100.0)
    assert (-100.0 <= response[2] <= 100.0)

    assert isinstance(response[0], float)
    assert isinstance(response[1], float)
    assert isinstance(response[2], float)

def test_compass():
    response = BirdbrainMicrobitInput.compass("A", "Compass")
    response = BirdbrainMicrobitInput.compass("A")

    assert (0 <= response <= 359)
    assert isinstance(response, int)

def test_magnetometer():
    response = BirdbrainMicrobitInput.magnetometer("A")

    assert (-180.0 <= response[0] <= 180.0)
    assert (-180.0 <= response[1] <= 180.0)
    assert (-180.0 <= response[2] <= 180.0)

    assert isinstance(response[0], int)
    assert isinstance(response[1], int)
    assert isinstance(response[2], int)

def test_button():
    assert not BirdbrainMicrobitInput.button("A", "A")
    assert not BirdbrainMicrobitInput.button("A", "B")
    assert not BirdbrainMicrobitInput.button("A", "LOGO")
    assert not BirdbrainMicrobitInput.button("A", "Logo")
    assert not BirdbrainMicrobitInput.button("A", "logo")

    with pytest.raises(BirdbrainException) as e:
        BirdbrainMicrobitInput.button("A", "BAD")
    assert e.value.message == "Error: Request to device failed"

def test_sound():
    response = BirdbrainMicrobitInput.sound("A")

    assert (0 <= response <= 100)
    assert isinstance(response, int)

def test_temperature():
    response = BirdbrainMicrobitInput.temperature("A")

    assert (0 <= response <= 50)
    assert isinstance(response, int)

def test_is_shaking():
    response = BirdbrainMicrobitInput.is_shaking("A")

    assert not response

def test_orientation():
    response = BirdbrainMicrobitInput.orientation("A")

    some_position = False
    for orientation in BirdbrainConstant.HUMMINGBIRD_ORIENTATION_RESULTS:
        some_position = some_position or (orientation == response)

    assert some_position
