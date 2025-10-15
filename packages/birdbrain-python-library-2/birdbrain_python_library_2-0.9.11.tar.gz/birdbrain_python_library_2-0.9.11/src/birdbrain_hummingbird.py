from birdbrain_hummingbird_input import BirdbrainHummingbirdInput
from birdbrain_hummingbird_output import BirdbrainHummingbirdOutput
from birdbrain_microbit import BirdbrainMicrobit
from birdbrain_microbit_input import BirdbrainMicrobitInput
from birdbrain_request import BirdbrainRequest

class BirdbrainHummingbird(BirdbrainMicrobit):
    """Hummingbird Bit Class includes the control of the outputs and inputs
        present on the Hummingbird Bit."""

    def __init__(self, device = 'A', raise_exception_if_no_connection = True):
        device_object = BirdbrainHummingbird.connect(device, raise_exception_if_no_connection)

        if not self.is_hummingbird():
            raise BirdbrainException("Device " + device + " is not a Hummingbird")

    def led(self, port, intensity):
        return BirdbrainHummingbirdOutput.led(self.device, port, intensity)

    def tri_led(self, port, r_int, g_int, b_int):
        return BirdbrainHummingbirdOutput.tri_led(self.device, port, r_int, g_int, b_int)

    def position_servo(self, port, angle):
        return BirdbrainHummingbirdOutput.position_servo(self.device, port, angle)

    def rotation_servo(self, port, speed):
        return BirdbrainHummingbirdOutput.rotation_servo(self.device, port, speed)

    def sensor(self, port):
        return BirdbrainHummingbirdInput.sensor(self.device, port)

    def light(self, port):
        return BirdbrainHummingbirdInput.light(self.device, port)

    def sound(self, port):
        return BirdbrainHummingbirdInput.sound(self.device, port)

    def distance(self, port):
        return BirdbrainHummingbirdInput.distance(self.device, port)

    def dial(self, port):
        return BirdbrainHummingbirdInput.dial(self.device, port)

    def voltage(self, port):
        return BirdbrainHummingbirdInput.voltage(self.device, port)

    def stop_all(self):
        BirdbrainRequest.stop_all(self.device)

    getDial = dial
    getDistance = distance
    setLED = led
    getLight = light
    setPositionServo = position_servo
    setRotationServo = rotation_servo
    getSound = sound
    getSensor = sensor
    stopAll = stop_all
    setTriLED = tri_led
    getVoltage = voltage
