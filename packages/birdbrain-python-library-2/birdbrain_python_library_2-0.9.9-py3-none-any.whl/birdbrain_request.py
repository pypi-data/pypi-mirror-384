import inspect
import time
import urllib.request

from birdbrain_constant import BirdbrainConstant
from birdbrain_exception import BirdbrainException
from birdbrain_utility import BirdbrainUtility

class BirdbrainRequest:
    @classmethod
    def uri(self, *args):
        return("http://127.0.0.1:30061/" + BirdbrainUtility.flatten_string(args))

    @classmethod
    def is_not_connected_response(self, response):
        return((response.lower() == "not connected"))

    @classmethod
    def response(self, *args):
        if "false" in args: return False

        try:
            if BirdbrainConstant.BIRDBRAIN_TEST: print("Test: URI", self.uri(*args))

            response_request = urllib.request.urlopen(self.uri(*args))
        except (ConnectionError, urllib.error.URLError, urllib.error.HTTPError):
            raise(BirdbrainException("Error: Request to device failed"))

        response = response_request.read().decode('utf-8').lower()

        if BirdbrainConstant.BIRDBRAIN_TEST: print("Test: response", response)

        if (self.is_not_connected_response(response)): raise(BirdbrainException("Error: The device is not connected"))

        time.sleep(0.01)  # hack to prevent http requests from overloading the BlueBird Connector

        return response

    @classmethod
    def response_status(self, *args):
        return BirdbrainRequest.request_status(BirdbrainRequest.response(args))

    @classmethod
    def is_connected(self, device):
        try:
            response = self.response('hummingbird', 'in', 'orientation', 'Shake', device)
        except BirdbrainException:
            return False

        return True

    @classmethod
    def is_not_connected(self, device):
        return(not self.is_connected(device))

    @classmethod
    def stop_all(self, device):
        return(self.request_status(self.response('hummingbird', 'out', 'stopall', device)))

    @classmethod
    def request_status(self, status):
     if BirdbrainConstant.BIRDBRAIN_TEST: print("Test: request status is", status)

     if status is None: return None

     if status == 'true': return(True)
     if status == 'led set': return(True)
     if status == 'triled set': return(True)
     if status == 'servo set': return(True)
     if status == 'buzzer set': return(True)
     if status == 'symbol set': return(True)
     if status == 'print set': return(True)
     if status == 'all stopped': return(True)

     if status == 'finch moved': return(True)
     if status == 'finch turned': return(True)
     if status == 'finch wheels started': return(True)
     if status == 'finch wheels stopped': return(True)
     if status == 'finch encoders reset': return(True)

     if status == 'false': return(False)
     if status == 'not connected': return(False)
     if status == 'invalid orientation': return(False)
     if status == 'invalid port': return(False)

     return(None)

    @classmethod
    def calculate_angle(self, intensity):
        return int(int(intensity) * 255 / 180)

    @classmethod
    def calculate_intensity(self, intensity):
        return int(int(BirdbrainUtility.bounds(intensity, 0, 100)) * 255 / 100)

    @classmethod
    def calculate_speed(self, speed):
        if int(speed) in range(-10, 10): return 255

        # QUESTION: why this calculation instead of normal mapping to 0..255 (and 255 means stop)
        # return ((int(speed) * 23 / 100) + 122)

        if int(speed) < 0:
            return int(119 - (-int(speed) / 100 * 45))
        else:
            return int((int(speed) / 100 * 25) + 121)

    @classmethod
    def calculate_left_or_right(self, direction):
        if direction == BirdbrainConstant.LEFT: return 'Left'
        if direction == BirdbrainConstant.RIGHT: return 'Right'

        return 'None'

    @classmethod
    def validate(self, validate, valid_range, validate_message):
        if not str(validate) in valid_range: raise BirdbrainException(validate_message)

        return True

    @classmethod
    def validate_port(self, port, valid_range, allow_all = False):
        if allow_all and str(port) == 'all': return True

        return BirdbrainRequest.validate(port, valid_range, f"Port {str(port)} out of range.")

    @classmethod
    def sensor_response(self, device, sensor, other = None, options = {}):
        if other is False: return False   # for invalid directions

        factor = options["factor"] if "factor" in options else BirdbrainConstant.DEFAULT_FACTOR
        min_response = options["min_response"] if "min_response" in options else BirdbrainConstant.DEFAULT_UNLIMITED_MIN_RESPONSE
        max_response = options["max_response"] if "max_response" in options else BirdbrainConstant.DEFAULT_UNLIMITED_MAX_RESPONSE
        type_method = options["type_method"] if "type_method" in options else BirdbrainConstant.DEFAULT_TYPE_METHOD

        request = ['hummingbird', 'in', sensor]
        if other is not None: request.append(other)
        request.append(device)

        response = (float(BirdbrainRequest.response(request)) * factor)

        response = round(BirdbrainUtility.decimal_bounds(response, min_response, max_response), 3)

        if type_method == 'int': return int(response)

        return response

    @classmethod
    def xyz_response(self, device, sensor, type_method = 'int'):
        x = round(float(BirdbrainRequest.response('hummingbird', 'in', sensor, 'X', device)), 3)
        y = round(float(BirdbrainRequest.response('hummingbird', 'in', sensor, 'Y', device)), 3)
        z = round(float(BirdbrainRequest.response('hummingbird', 'in', sensor, 'Z', device)), 3)

        if type_method == 'int':
            return [int(x), int(y), int(z)]
        else:
            return [float(x), float(y), float(z)]

    @classmethod
    def tri_led_response(self, device, port, r_intensity, g_intensity, b_intensity, valid_range, allow_all = False):
        """Set TriLED  of a certain port requested to a valid intensity."""
        self.validate_port(port, valid_range, allow_all)

        calc_r = BirdbrainRequest.calculate_intensity(r_intensity)
        calc_g = BirdbrainRequest.calculate_intensity(g_intensity)
        calc_b = BirdbrainRequest.calculate_intensity(b_intensity)

        return BirdbrainRequest.response_status('hummingbird', 'out', 'triled', port, calc_r, calc_g, calc_b, device)

    @classmethod
    def orientation_response(self, device, sensor, orientations, orientation_results, orientation_in_between):
        for index, target_orientation in enumerate(orientations):
            response = self.response("hummingbird", "in", sensor, target_orientation, device)

            if (response == "true"): return orientation_results[index]

        return orientation_in_between
