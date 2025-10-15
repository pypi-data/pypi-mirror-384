from birdbrain_constant import BirdbrainConstant
from birdbrain_device import BirdbrainDevice
from birdbrain_microbit_input import BirdbrainMicrobitInput
from birdbrain_request import BirdbrainRequest
from birdbrain_utility import BirdbrainUtility

class BirdbrainFinchInput(BirdbrainRequest):
    @classmethod
    def is_moving(self, device):
        return BirdbrainRequest.request_status(BirdbrainRequest.response('hummingbird', 'in', 'finchIsMoving', 'static', device))

    @classmethod
    def light(self, device, side):
        """Read the value of the right or left light sensor ('R' or 'L')."""

        return self.sensor_response(device, 'Light', BirdbrainRequest.calculate_left_or_right(side))

    @classmethod
    def distance(self, device):
        """Read the value of the distance sensor"""

        distance_options = {}
        distance_options['factor'] = BirdbrainConstant.DISTANCE_FACTOR  # was 0.0919
        distance_options['min_response'] = BirdbrainConstant.DEFAULT_UNLIMITED_MIN_RESPONSE
        distance_options['max_response'] = BirdbrainConstant.DEFAULT_UNLIMITED_MAX_RESPONSE

        return self.sensor_response(device, 'Distance', 'static', distance_options)

    @classmethod
    def line(self, device, side):
        """Read the value of the right or left line sensor ('R' or 'L').
        Returns brightness as a value 0-100 where a larger number
        represents more reflected light."""

        return self.sensor_response(device, 'Line', BirdbrainRequest.calculate_left_or_right(side))

    @classmethod
    def encoder(self, device, side):
        """Read the value of the right or left encoder ('R' or 'L').
        Values are returned in rotations."""

        sensor_options = {}
        sensor_options['min_response'] = float(BirdbrainConstant.DEFAULT_UNLIMITED_MIN_RESPONSE)
        sensor_options['max_response'] = float(BirdbrainConstant.DEFAULT_UNLIMITED_MAX_RESPONSE)
        sensor_options['type_method'] = 'float'

        return round(self.sensor_response(device, 'Encoder', BirdbrainRequest.calculate_left_or_right(side), sensor_options), 2)

    @classmethod
    def orientation(self, device):
        """Return the orentation of the Finch. Results found in BirdbrainConstant.FINCH_ORIENTATION_RESULTS"""
        return self.orientation_response(device, "finchOrientation", BirdbrainConstant.FINCH_ORIENTATIONS, 
            BirdbrainConstant.FINCH_ORIENTATION_RESULTS, BirdbrainConstant.FINCH_ORIENTATION_IN_BETWEEN)

    # The following methods override those within the Microbit
    # class to return values within the Finch reference frame.
    @classmethod
    def acceleration(self, device):
        """Gives the acceleration of X,Y,Z in m/sec2, relative
        to the Finch's position."""

        return BirdbrainMicrobitInput.acceleration(device, "finchAccel")

    @classmethod
    def compass(self, device):
        """Returns values 0-359 indicating the orentation of the Earth's
        magnetic field, relative to the Finch's position."""

        return BirdbrainMicrobitInput.compass(device, "finchCompass")

    @classmethod
    def magnetometer(self, device):
        """Return the values of X,Y,Z of a magnetommeter, relative to the Finch's position."""

        return BirdbrainMicrobitInput.magnetometer(device, "finchMag")

