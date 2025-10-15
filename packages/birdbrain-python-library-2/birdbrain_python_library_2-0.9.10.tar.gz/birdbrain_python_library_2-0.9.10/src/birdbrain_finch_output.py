import time

from birdbrain_constant import BirdbrainConstant
from birdbrain_finch_input import BirdbrainFinchInput
from birdbrain_request import BirdbrainRequest
from birdbrain_utility import BirdbrainUtility

class BirdbrainFinchOutput(BirdbrainRequest):
    @classmethod
    def beak(self, device, r_intensity, g_intensity, b_intensity):
        """Set beak to a valid intensity. Each intensity should be an integer from 0 to 100."""
        return self.tri_led_response(device, 1, r_intensity, g_intensity, b_intensity, BirdbrainConstant.VALID_BEAK_PORTS)

    @classmethod
    def tail(self, device, port, r_intensity, g_intensity, b_intensity):
        """Set tail to a valid intensity. Port can be specified as 1, 2, 3, 4, or all.
        Each intensity should be an integer from 0 to 100."""

        if not port == "all":
            port = int(port) + 1  # tail starts counting at 2

        return self.tri_led_response(device, port, r_intensity, g_intensity, b_intensity, BirdbrainConstant.VALID_TAIL_PORTS, True)

    @classmethod
    def move(self, device, direction, distance, speed, wait_to_finish_movement = True):
        """Move the Finch forward or backward for a given distance at a given speed.
        Direction should be specified as 'F' or 'B'."""
        calc_direction = None

        if direction == BirdbrainConstant.FORWARD: calc_direction = 'Forward'
        if direction == BirdbrainConstant.BACKWARD: calc_direction = 'Backward'

        calc_distance = BirdbrainUtility.bounds(distance, -10000, 10000)
        calc_speed = BirdbrainUtility.bounds(speed, 0, 100)

        return self.__move_and_wait(device, wait_to_finish_movement, 'hummingbird', 'out', 'move', device, calc_direction, calc_distance, calc_speed)

    @classmethod
    def turn(self, device, direction, angle, speed, wait_to_finish_movement = True):
        """Turn the Finch right or left to a given angle at a given speed.
        Direction should be specified as 'R' or 'L'."""
        calc_direction = BirdbrainRequest.calculate_left_or_right(direction)
        calc_angle = BirdbrainUtility.bounds(angle, 0, 360)
        calc_speed = BirdbrainUtility.bounds(speed, 0, 100)

        return self.__move_and_wait(device, wait_to_finish_movement, 'hummingbird', 'out', 'turn', device, calc_direction, calc_angle, calc_speed)

    @classmethod
    def wait(self, device):
        timeout_time = time.time() + BirdbrainConstant.MOVE_TIMEOUT_SECONDS

        while (timeout_time > time.time()) and (BirdbrainFinchInput.is_moving(device)):
            time.sleep(BirdbrainConstant.MOVE_CHECK_MOVING_DELAY)

        return True

    @classmethod
    def motors(self, device, left_speed, right_speed):
        """Set the speed of each motor individually. Speed should be in
        the range of -100 to 100."""

        left_speed = BirdbrainUtility.bounds(left_speed, -100, 100)
        right_speed = BirdbrainUtility.bounds(right_speed, -100, 100)

        return BirdbrainRequest.response_status('hummingbird', 'out', 'wheels', device, left_speed, right_speed)

    @classmethod
    def stop(self, device):
        """Stop the Finch motors."""

        return BirdbrainRequest.response_status('hummingbird', 'out', 'stopFinch', device)

    @classmethod
    def reset_encoders(self, device):
        """Reset both encoder values to 0."""

        response = BirdbrainRequest.response_status('hummingbird', 'out', 'resetEncoders', device)

        time.sleep(BirdbrainConstant.RESET_ENCODERS_DELAY)  #  finch needs a chance to actually reset

        return response

    @classmethod
    def __move_and_wait(self, device, wait_to_finish_movement, *args):
        response = BirdbrainRequest.response_status(*args)

        time.sleep(BirdbrainConstant.MOVE_START_WAIT_SECONDS)  # hack to give time to start before waiting

        if wait_to_finish_movement: self.wait(device)

        return response
