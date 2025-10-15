import inspect

from birdbrain_constant import BirdbrainConstant
from birdbrain_request import BirdbrainRequest

class BirdbrainMicrobitInput(BirdbrainRequest):
    @classmethod
    def acceleration(self, device, sensor = "Accelerometer"):
        """Gives the acceleration of X,Y,Z in m/sec2."""

        return self.xyz_response(device, sensor, "float")

    @classmethod
    def compass(self, device, sensor = 'Compass'):
        """Returns values 0-359 indicating the orentation of the Earth's
        magnetic field."""

        sensor_options = {}
        sensor_options['min_response'] = BirdbrainConstant.DEFAULT_DEGREES_MIN_RESPONSE
        sensor_options['max_response'] = BirdbrainConstant.DEFAULT_DEGREES_MAX_RESPONSE

        compass_option = None if sensor == 'Compass' else 'static'

        return self.sensor_response(device, sensor, compass_option, sensor_options)

    @classmethod
    def magnetometer(self, device, sensor = "Magnetometer"):
        """Return the values of X,Y,Z of a magnetommeter."""
        return self.xyz_response(device, sensor, "int")

    @classmethod
    def button(self, device, button):
        """Return the status of the button asked. Specify button 'A', 'B', or
        'Logo'. Logo available for V2 micro:bit only."""

        return self.request_status(self.response('hummingbird', 'in', 'button', button.capitalize(), device))

    @classmethod
    def sound(self, device):
        """Return the current sound level as an integer between 1 and 100.
        Available for V2 micro:bit only."""

        response = self.response('hummingbird', 'in', "V2sensor", "Sound", device)

        if response == 'micro:bit v2 required': return 0

        return int(response)

    @classmethod
    def temperature(self, device):
        """Return the current temperature as an integer in degrees Celcius.
        Available for V2 micro:bit only."""

        response = self.response('hummingbird', 'in', "V2sensor", "Temperature", device)

        if response == 'micro:bit v2 required': return 0

        return int(response)

    @classmethod
    def is_shaking(self, device):
        """Return true if the device is shaking, false otherwise."""

        return self.request_status(self.response('hummingbird', 'in', 'orientation', 'Shake', device))

    @classmethod
    def orientation(self, device):
        """Return the orentation of the Microbit. Results found in BirdbrainConstant.HUMMINGBIRD_ORIENTATION_RESULTS"""
        return self.orientation_response(device, "orientation", BirdbrainConstant.HUMMINGBIRD_ORIENTATIONS, 
            BirdbrainConstant.HUMMINGBIRD_ORIENTATION_RESULTS, BirdbrainConstant.HUMMINGBIRD_ORIENTATION_IN_BETWEEN)
