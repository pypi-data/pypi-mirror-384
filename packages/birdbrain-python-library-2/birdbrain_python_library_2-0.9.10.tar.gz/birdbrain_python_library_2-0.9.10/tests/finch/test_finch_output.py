import pytest
import time

from birdbrain_constant import BirdbrainConstant
from birdbrain_exception import BirdbrainException
from birdbrain_finch import BirdbrainFinch
from birdbrain_finch_output import BirdbrainFinchOutput
from birdbrain_request import BirdbrainRequest

def test_beak():
    assert BirdbrainFinchOutput.beak("B", 10, 50, 50)
    time.sleep(0.15)
    assert BirdbrainFinchOutput.beak("B", 0, 0, 0)

def test_tail():
    assert BirdbrainFinchOutput.tail("B", 1, 10, 50, 50)
    time.sleep(0.1)
    assert BirdbrainFinchOutput.tail("B", 1, "0", 50, "0")
    time.sleep(0.1)
    assert BirdbrainFinchOutput.tail("B", "2", "0", 50, "0")
    time.sleep(0.1)
    assert BirdbrainFinchOutput.tail("B", 3, "0", 50, "0")
    time.sleep(0.1)
    assert BirdbrainFinchOutput.tail("B", 4, "0", 50, "0")
    time.sleep(0.1)
    assert BirdbrainFinchOutput.tail("B", "all", 0, 0, 100)
    time.sleep(0.1)
    assert BirdbrainFinchOutput.tail("B", "all", 0, 0, 0)

def test_move():
    assert BirdbrainFinchOutput.move("B", BirdbrainConstant.FORWARD, 4, 5)
    assert BirdbrainFinchOutput.move("B", BirdbrainConstant.FORWARD, "4", "5")

    assert BirdbrainFinchOutput.move("B", BirdbrainConstant.BACKWARD, 4, 5)
    assert BirdbrainFinchOutput.move("B", BirdbrainConstant.BACKWARD, "4", "5")

    with pytest.raises(BirdbrainException):
        assert BirdbrainFinchOutput.move("B", "BAD", 4, 5)
        assert e.value.message == "Error: Request to device failed"

    with pytest.raises(BirdbrainException) as e:
        assert BirdbrainFinchOutput.move("B", None, 4, 5)
        assert e.value.message == "Error: Request to device failed"

    BirdbrainRequest.stop_all("B")

def test_turn():
    assert BirdbrainFinchOutput.turn("B", "L", 25, 50)
    assert BirdbrainFinchOutput.turn("B", "R", 25, 50)
    assert BirdbrainFinchOutput.turn("B", "L", "25", 50)
    assert BirdbrainFinchOutput.turn("B", "R", 25, "50")

    with pytest.raises(BirdbrainException):
        assert BirdbrainFinchOutput.turn("B", "BAD", 90, 50)
        assert e.value.message == "Error: Request to device failed"

def test_motors():
    assert BirdbrainFinchOutput.motors("B", 25, 0)
    time.sleep(0.2)
    assert BirdbrainFinchOutput.motors("B", -25, 0)
    time.sleep(0.2)

    assert BirdbrainFinchOutput.motors("B", 0, -25)
    time.sleep(0.2)
    assert BirdbrainFinchOutput.motors("B", "0", "25")
    time.sleep(0.2)

    BirdbrainRequest.stop_all("B")

def test_stop():
    assert BirdbrainFinchOutput.move("B", BirdbrainConstant.FORWARD, 99999, 5, False)
    time.sleep(0.2)
    assert BirdbrainFinchOutput.stop("B")

    assert BirdbrainFinchOutput.move("B", BirdbrainConstant.BACKWARD, 99999, 5, False)
    time.sleep(0.2)
    assert BirdbrainFinchOutput.stop("B")

def test_reset_encoders():
    assert BirdbrainFinchOutput.reset_encoders("B")
