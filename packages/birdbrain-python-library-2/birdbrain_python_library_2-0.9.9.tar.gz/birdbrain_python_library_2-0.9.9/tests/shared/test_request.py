import pytest

from birdbrain_constant import BirdbrainConstant
from birdbrain_exception import BirdbrainException
from birdbrain_request import BirdbrainRequest

def test_request_uri():
    uri = BirdbrainRequest.uri(["in", "1", "2", "3", "4", [ "99", 99 ], "something"])

    assert uri == "http://127.0.0.1:30061/in/1/2/3/4/99/99/something"

def test_connected():
    assert BirdbrainRequest.is_connected("A")

def test_not_connected():
    assert not BirdbrainRequest.is_connected("C")

def test_not_connected_connected():
    assert not BirdbrainRequest.is_not_connected("A")

def test_not_connected_not_connected():
    assert BirdbrainRequest.is_not_connected("C")

def test_response_with_false_arg():
    assert not BirdbrainRequest.response("1", "false", "2")

def test_response():
    assert BirdbrainRequest.response("hummingbird", "in", "orientation", "Shake", "A")

def test_response_status():
    assert not BirdbrainRequest.response_status("hummingbird", "in", "orientation", "Shake", "A")

def test_response_no_connection():
    with pytest.raises(BirdbrainException) as e:
        response = BirdbrainRequest.response("hummingbird", "in", "orientation", "Shake", "C")

    assert e.value.message == "Error: The device is not connected"

def test_request_status():
    assert BirdbrainRequest.request_status("all stopped")

def test_stop_all():
    response = BirdbrainRequest.stop_all("A")

    assert response

def test_disconnect():
    with pytest.raises(BirdbrainException) as e:
        BirdbrainRequest.stop_all("C")

    assert e.value.message == "Error: The device is not connected"

def test_xyz_response_no_connection():
    with pytest.raises(BirdbrainException) as e:
        response = BirdbrainRequest.xyz_response("C", "Accelerometer")

def test_xyz_response():
    xyz = BirdbrainRequest.xyz_response("A", "Accelerometer", "float")

    assert isinstance(xyz, list)
    assert len(xyz) == 3

def test_calculate_speed():
    assert BirdbrainRequest.calculate_speed(0) == 255
    assert BirdbrainRequest.calculate_speed(9) == 255
    assert BirdbrainRequest.calculate_speed(100) == 146.0
    assert BirdbrainRequest.calculate_speed(-100) == 74.0

    assert BirdbrainRequest.calculate_speed("0") == 255
    assert BirdbrainRequest.calculate_speed("9") == 255
    assert BirdbrainRequest.calculate_speed("100") == 146.0
    assert BirdbrainRequest.calculate_speed("-100") == 74.0

def test_calculate_left_or_right():
    assert BirdbrainRequest.calculate_left_or_right('L') == 'Left'
    assert BirdbrainRequest.calculate_left_or_right('R') == 'Right'
    assert BirdbrainRequest.calculate_left_or_right('BAD') == 'None'

def test_validate_port():
    assert BirdbrainRequest.validate_port(1, BirdbrainConstant.VALID_LED_PORTS)
    assert BirdbrainRequest.validate_port(2, BirdbrainConstant.VALID_LED_PORTS)
    assert BirdbrainRequest.validate_port(3, BirdbrainConstant.VALID_LED_PORTS)
    assert BirdbrainRequest.validate_port("1", BirdbrainConstant.VALID_LED_PORTS)

    with pytest.raises(BirdbrainException) as e:
        BirdbrainRequest.validate_port(4, BirdbrainConstant.VALID_LED_PORTS)
    with pytest.raises(BirdbrainException) as e:
        BirdbrainRequest.validate_port(-1, BirdbrainConstant.VALID_LED_PORTS)
    with pytest.raises(BirdbrainException) as e:
        BirdbrainRequest.validate_port("4", BirdbrainConstant.VALID_LED_PORTS)
