from birdbrain_device import BirdbrainDevice
from birdbrain_exception import BirdbrainException
from birdbrain_microbit_input import BirdbrainMicrobitInput
from birdbrain_microbit_output import BirdbrainMicrobitOutput
from birdbrain_request import BirdbrainRequest

class BirdbrainMicrobit(BirdbrainDevice):
    def __init__(self, device = 'A', raise_exception_if_no_connection = True):
        self.device_object = BirdbrainMicrobit.connect(device, raise_exception_if_no_connection)

        if not self.is_microbit():
            raise BirdbrainException("Error: Device " + device + " is not a Microbit")

    def display(self, list):
        return BirdbrainMicrobitOutput.display(self.state, self.device, list)

    def clear_display(self):
        return BirdbrainMicrobitOutput.clear_display(self.state, self.device)

    def point(self, x, y, value):
        return BirdbrainMicrobitOutput.point(self.state, self.device, x, y, value)

    def print(self, message):
        return BirdbrainMicrobitOutput.print(self.state, self.device, message)

    def play_note(self, note, beats):
        return BirdbrainMicrobitOutput.play_note(self.device, note, beats)

    def beep(self):
        return BirdbrainMicrobitOutput.play_note(self.device, 80, 0.333)

    def acceleration(self):
        return BirdbrainMicrobitInput.acceleration(self.device)

    def compass(self):
        return BirdbrainMicrobitInput.compass(self.device)

    def magnetometer(self):
        return BirdbrainMicrobitInput.magnetometer(self.device)

    def button(self, button):
        return BirdbrainMicrobitInput.button(self.device, button)

    def sound(self, port = None):
        return BirdbrainMicrobitInput.sound(self.device)

    def temperature(self):
        return BirdbrainMicrobitInput.temperature(self.device)

    def is_shaking(self):
        return BirdbrainMicrobitInput.is_shaking(self.device)

    def orientation(self):
        return BirdbrainMicrobitInput.orientation(self.device)

    def stop_all(self):
        BirdbrainRequest.stop_all(self.device)

    getAcceleration = acceleration
    getButton = button
    getCompass = compass
    setDisplay = display
    isShaking = is_shaking
    getMagnetometer = magnetometer
    getOrientation = orientation
    playNote = play_note
    setPoint = point
    getSound = sound
    stopAll = stop_all
    getTemperature = temperature
