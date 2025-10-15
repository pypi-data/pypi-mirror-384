from birdbrain_constant import BirdbrainConstant
from birdbrain_microbit_input import BirdbrainMicrobitInput
from birdbrain_request import BirdbrainRequest

class BirdbrainHummingbirdInput(BirdbrainRequest):
    @classmethod
    def acceleration(self, device):
        """Gives the acceleration of X,Y,Z in m/sec2, relative
        to the Finch's position."""

        return BirdbrainMicrobitInput.acceleration(device)

    @classmethod
    def compass(self, device):
        """Returns values 0-359 indicating the orentation of the Earth's
        magnetic field, relative to the Finch's position."""

        return BirdbrainMicrobitInput.compass(device)

    @classmethod
    def magnetometer(self, device):
        """Return the values of X,Y,Z of a magnetommeter, relative to the Finch's position."""

        return BirdbrainMicrobitInput.magnetometer(device)

    @classmethod
    def orientation(self, device):
        """Return the orentation of the Hummingbird. Results found in BirdbrainConstant.HUMMINGBIRD_ORIENTATION_RESULTS"""

        return BirdbrainMicrobitInput.orientation(device)

    @classmethod
    def sensor(self, device, port):
        """Read the value of the sensor attached to a certain port."""

        sensor_options = {}
        sensor_options['min_response'] = BirdbrainConstant.DEFAULT_UNLIMITED_MIN_RESPONSE
        sensor_options['max_response'] = BirdbrainConstant.DEFAULT_UNLIMITED_MAX_RESPONSE
        sensor_options['type_method'] = 'float'

        return self.sensor_response(device, 'sensor', port, sensor_options)

    @classmethod
    def light(self, device, port):
        """Read the value of the light sensor attached to a certain port."""

        sensor_options = {}
        sensor_options['factor'] = BirdbrainConstant.LIGHT_FACTOR
        sensor_options['min_response'] = BirdbrainConstant.DEFAULT_MIN_RESPONSE
        sensor_options['max_response'] = BirdbrainConstant.DEFAULT_MAX_RESPONSE

        return self.sensor_response(device, 'sensor', port, sensor_options)

    @classmethod
    def sound(self, device, port):
        """Read the value of the sound sensor attached to a certain port."""

        port = str(port).lower()

        if port == "microbit" or port == "micro:bit":
            return BirdbrainMicrobitInput.sound(device)

        sensor_options = {}
        sensor_options['factor'] = BirdbrainConstant.SOUND_FACTOR
        sensor_options['min_response'] = BirdbrainConstant.DEFAULT_MIN_RESPONSE
        sensor_options['max_response'] = BirdbrainConstant.DEFAULT_MAX_RESPONSE

        return self.sensor_response(device, 'sensor', port, sensor_options)

    @classmethod
    def distance(self, device, port):
        """Read the value of the distance sensor attached to a certain port."""

        sensor_options = {}
        sensor_options['factor'] = BirdbrainConstant.DISTANCE_FACTOR
        sensor_options['min_response'] = BirdbrainConstant.DEFAULT_MIN_RESPONSE
        sensor_options['max_response'] = BirdbrainConstant.DEFAULT_UNLIMITED_MAX_RESPONSE

        return self.sensor_response(device, 'sensor', port, sensor_options)

    @classmethod
    def dial(self, device, port):
        """Read the value of the dial attached to a certain port."""

        sensor_options = {}
        sensor_options['factor'] = BirdbrainConstant.DIAL_FACTOR
        sensor_options['min_response'] = BirdbrainConstant.DEFAULT_MIN_RESPONSE
        sensor_options['max_response'] = BirdbrainConstant.DEFAULT_MAX_RESPONSE

        return self.sensor_response(device, 'sensor', port, sensor_options)

    @classmethod
    def voltage(self, device, port):
        """Read the value of  the dial attached to a certain port."""

        sensor_options = {}
        sensor_options['factor'] = BirdbrainConstant.VOLTAGE_FACTOR
        sensor_options['min_response'] = BirdbrainConstant.VOLTAGE_MIN
        sensor_options['max_response'] = BirdbrainConstant.VOLTAGE_MAX
        sensor_options['type_method'] = 'float'

        return self.sensor_response(device, 'sensor', port, sensor_options)
