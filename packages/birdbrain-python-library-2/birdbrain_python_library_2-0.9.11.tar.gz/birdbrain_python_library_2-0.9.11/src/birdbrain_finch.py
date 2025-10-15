from birdbrain_constant import BirdbrainConstant
from birdbrain_exception import BirdbrainException
from birdbrain_finch_input import BirdbrainFinchInput
from birdbrain_finch_output import BirdbrainFinchOutput
from birdbrain_microbit import BirdbrainMicrobit
from birdbrain_microbit_input import BirdbrainMicrobitInput

class BirdbrainFinch(BirdbrainMicrobit):
    """The Finch class includes the control of the outputs and inputs present
    in the Finch robot. When creating an instance, specify which robot by the
    device letter used in the BlueBirdConnector device list (A, B, or C)."""

    def __init__(self, device='A', raise_exception_if_no_connection = True):
        self.device_object = BirdbrainFinch.connect(device, raise_exception_if_no_connection)

        if not self.is_finch():
            raise BirdbrainException("Error: Device " + device + " is not a Finch")

    def is_moving(self):
        return BirdbrainFinchInput.is_moving(self.device)

    def beak(self, r_intensity, g_intensity, b_intensity):
        return BirdbrainFinchOutput.beak(self.device, r_intensity, g_intensity, b_intensity)

    def tail(self, port, r_intensity, g_intensity, b_intensity):
        return BirdbrainFinchOutput.tail(self.device, port, r_intensity, g_intensity, b_intensity)

    def move(self, direction, distance, speed, wait_to_finish_movement = True):
        return BirdbrainFinchOutput.move(self.device, direction, distance, speed, wait_to_finish_movement)

    def turn(self, direction, angle, speed, wait_to_finish_movement = True):
        return BirdbrainFinchOutput.turn(self.device, direction, angle, speed, wait_to_finish_movement)

    def motors(self, left_speed, right_speed):
        return BirdbrainFinchOutput.motors(self.device, left_speed, right_speed)

    def wait(self, device):
        return BirdbrainFinchOutput.wait(self.device)

    def stop(self):
        return BirdbrainFinchOutput.stop(self.device)

    def reset_encoders(self):
        return BirdbrainFinchOutput.reset_encoders(self.device)

    def light(self, side):
        return BirdbrainFinchInput.light(self.device, side)

    def distance(self):
        return BirdbrainFinchInput.distance(self.device)

    def line(self, side):
        return BirdbrainFinchInput.line(self.device, side)

    def encoder(self, side):
        return BirdbrainFinchInput.encoder(self.device, side)

    def orientation(self):
        return BirdbrainFinchInput.orientation(self.device)

    def acceleration(self):
        return BirdbrainFinchInput.acceleration(self.device)

    def compass(self):
        return BirdbrainFinchInput.compass(self.device)

    def magnetometer(self):
        return BirdbrainFinchInput.magnetometer(self.device)

    getAcceleration = acceleration
    setBeak = beak
    getCompass = compass
    getDistance = distance
    getEncoder = encoder
    getLight = light
    getLine = line
    getMagnetometer = magnetometer
    setMotors = motors
    setMove = move
    getOrientation = orientation
    resetEncoders = reset_encoders
    setTail = tail
    setTurn = turn
