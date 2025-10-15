from birdbrain_constant import BirdbrainConstant
from birdbrain_request import BirdbrainRequest
from birdbrain_utility import BirdbrainUtility

class BirdbrainHummingbirdOutput(BirdbrainRequest):
    @classmethod
    def led(self, device, port, intensity):
        """Set led  of a certain port requested to a valid intensity."""
        self.validate_port(port, BirdbrainConstant.VALID_LED_PORTS)

        calculated_intensity = BirdbrainUtility.bounds(BirdbrainRequest.calculate_intensity(intensity), 0, 255)

        return BirdbrainRequest.response_status('hummingbird', 'out', 'led', port, calculated_intensity, device)

    @classmethod
    def tri_led(self, device, port, r_intensity, g_intensity, b_intensity):
        """Set TriLED  of a certain port requested to a valid intensity."""
        return self.tri_led_response(device, port, r_intensity, g_intensity, b_intensity, BirdbrainConstant.VALID_TRI_LED_PORTS)

    @classmethod
    def position_servo(self, device, port, angle):
        """Set Position servo of a certain port requested to a valid angle."""
        BirdbrainRequest.validate_port(port, BirdbrainConstant.VALID_SERVO_PORTS)

        calculated_angle = BirdbrainUtility.bounds(BirdbrainRequest.calculate_angle(angle), 0, 254)

        return BirdbrainRequest.response_status('hummingbird', 'out', 'servo', port, calculated_angle, device)

    @classmethod
    def rotation_servo(self, device, port, speed):
        """Set Rotation servo of a certain port requested to a valid speed."""
        BirdbrainRequest.validate_port(port, BirdbrainConstant.VALID_SERVO_PORTS)

        calculated_speed = BirdbrainRequest.calculate_speed(BirdbrainUtility.bounds(int(speed), -100, 100))

        return BirdbrainRequest.response_status('hummingbird', 'out', 'rotation', port, calculated_speed, device)
