import pytest
import time

from birdbrain_device import BirdbrainDevice
from birdbrain_exception import BirdbrainException
from birdbrain_microbit import BirdbrainMicrobit
from birdbrain_microbit_output import BirdbrainMicrobitOutput
from birdbrain_request import BirdbrainRequest
from birdbrain_state import BirdbrainState

def test_display():
    state = BirdbrainState()

    BirdbrainMicrobitOutput.display(state, "A", [ 0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0 ])

    time.sleep(0.15)

    BirdbrainRequest.stop_all("A")

def test_display_wrong_size():
    with pytest.raises(BirdbrainException) as e:
        state = BirdbrainState()

        list = [ 0,1 ]

        BirdbrainMicrobitOutput.display(state, "A", list)
    assert e.value.message == "Error: display() requires a list of length 25"

def test_point_and_clear_display():
    state = BirdbrainState()

    for i in range(2):
        assert BirdbrainMicrobitOutput.point(state, "A", 1, 1, 1)
        assert BirdbrainMicrobitOutput.point(state, "A", 1, 5, 1)
        assert BirdbrainMicrobitOutput.point(state, "A", 5, 1, 1)
        assert BirdbrainMicrobitOutput.point(state, "A", 5, 5, 1)

        time.sleep(0.15)

        BirdbrainMicrobitOutput.clear_display(state, "A")

def test_point_true_or_false():
    state = BirdbrainState()

    assert BirdbrainMicrobitOutput.point(state, "A", 3, 3, True)

    time.sleep(0.15)

    assert BirdbrainMicrobitOutput.point(state, "A", 3, 3, False)

def test_point_out_of_range():
    with pytest.raises(BirdbrainException) as e:
        state = BirdbrainState()

        assert BirdbrainMicrobitOutput.point(state, "A", 999, 1, 1)
    assert e.value.message == "Error: point out of range"

def test_print():
    state = BirdbrainState()

    assert BirdbrainMicrobitOutput.print(state, "A", "B")
    time.sleep(1)

    assert BirdbrainMicrobitOutput.print(state, "A", " ")
    time.sleep(1)

def test_print_nothing():
    state = BirdbrainState()

    assert BirdbrainMicrobitOutput.print(state, "A", "")
    time.sleep(1)

    assert BirdbrainMicrobitOutput.print(state, "A", None)
    time.sleep(1)

def test_play_note():
    assert BirdbrainMicrobitOutput.play_note("A", 50, 0.25)
