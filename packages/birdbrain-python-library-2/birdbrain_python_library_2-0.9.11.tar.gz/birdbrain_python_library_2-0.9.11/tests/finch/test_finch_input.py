import pytest
import time

from birdbrain_constant import BirdbrainConstant
from birdbrain_exception import BirdbrainException
from birdbrain_finch import BirdbrainFinch
from birdbrain_finch_input import BirdbrainFinchInput
from birdbrain_finch_output import BirdbrainFinchOutput
from birdbrain_request import BirdbrainRequest

def test_is_moving():
    assert BirdbrainFinchOutput.move("B", BirdbrainConstant.FORWARD, 7, 5, False)
    assert BirdbrainFinchInput.is_moving("B")

    BirdbrainFinchOutput.wait("B")

    assert BirdbrainFinchOutput.move("B", BirdbrainConstant.BACKWARD, 7, 5, True)

    assert BirdbrainRequest.stop_all("B")

    assert not BirdbrainFinchInput.is_moving("B")

def test_light():
    response = BirdbrainFinchInput.light("B", "L")

    assert (0 <= response <= 100)
    assert isinstance(response, int)

    response = BirdbrainFinchInput.light("B", "R")

    assert (0 <= response <= 100)
    assert isinstance(response, int)

    with pytest.raises(BirdbrainException) as e:
        BirdbrainFinchInput.light("B", "BAD")
    assert e.value.message == "Error: Request to device failed"

    with pytest.raises(BirdbrainException) as e:
        BirdbrainFinchInput.light("B", None)
    assert e.value.message == "Error: Request to device failed"

def test_distance():
    response = BirdbrainFinchInput.distance("B")

    assert (0 <= response <= 298)
    assert isinstance(response, int)

def test_line():
    response = BirdbrainFinchInput.line("B", "L")

    assert (0 <= response <= 100)
    assert isinstance(response, int)

    response = BirdbrainFinchInput.line("B", "R")

    assert (0 <= response <= 100)
    assert isinstance(response, int)

    with pytest.raises(BirdbrainException) as e:
        BirdbrainFinchInput.line("B", "BAD")
    assert e.value.message == "Error: Request to device failed"

    with pytest.raises(BirdbrainException) as e:
        BirdbrainFinchInput.line("B", None)
    assert e.value.message == "Error: Request to device failed"

def test_encoder():
    response = BirdbrainFinchInput.encoder("B", "L")

    assert (-100.0 <= response <= 100.0)
    assert isinstance(response, float)

    response = BirdbrainFinchInput.encoder("B", "R")

    assert (-100.0 <= response <= 100.0)
    assert isinstance(response, float)

    with pytest.raises(BirdbrainException) as e:
        BirdbrainFinchInput.encoder("B", "BAD")
    assert e.value.message == "Error: Request to device failed"

    with pytest.raises(BirdbrainException) as e:
        BirdbrainFinchInput.encoder("B", None)
    assert e.value.message == "Error: Request to device failed"

def test_acceleration():
    response = BirdbrainFinchInput.acceleration("B")

    assert (-100.0 <= response[0] <= 100.0)
    assert (-100.0 <= response[1] <= 100.0)
    assert (-100.0 <= response[2] <= 100.0)

    assert isinstance(response[0], float)
    assert isinstance(response[1], float)
    assert isinstance(response[2], float)

def test_compass():
    response = BirdbrainFinchInput.compass("B")

    assert (0 <= response <= 359)
    assert isinstance(response, int)

def test_magnetometer():
    response = BirdbrainFinchInput.magnetometer("B")

    assert (-180.0 <= response[0] <= 180.0)
    assert (-180.0 <= response[1] <= 180.0)
    assert (-180.0 <= response[2] <= 180.0)

    assert isinstance(response[0], int)
    assert isinstance(response[1], int)
    assert isinstance(response[2], int)

def test_orientation():
    response = BirdbrainFinchInput.orientation("B")

    some_position = False
    for orientation in BirdbrainConstant.FINCH_ORIENTATION_RESULTS:
        some_position = some_position or (orientation == response)

    assert some_position
