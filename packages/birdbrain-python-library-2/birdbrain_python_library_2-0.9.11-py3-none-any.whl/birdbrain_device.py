from birdbrain_constant import BirdbrainConstant
from birdbrain_exception import BirdbrainException
from birdbrain_request import BirdbrainRequest
from birdbrain_state import BirdbrainState

class BirdbrainDevice:
    def __init__(self, device = "A", raise_exception_if_no_connection = True):
        self.state = BirdbrainState()
        self.device = BirdbrainDevice.remap_device(device)
        self.connected = False

    @classmethod
    def connect(self, device = "A", raise_exception_if_no_connection = True):
        device_object = BirdbrainDevice(device)

        self.state = device_object.state
        self.device = device_object.device
        self.connected = device_object.connected

        if device is None:
            raise BirdbrainException("Missing device name")
        if not device in BirdbrainConstant.VALID_DEVICES:
            raise BirdbrainException("Invalid device name: " + device)

        self.connected = device_object.connect_device()

        if raise_exception_if_no_connection and not device_object.connected:
            raise BirdbrainException("No connection: " + device)

        return device_object

    def is_connected(self):
        """Determine if the device is connected"""

        return self.connected

    def __is_device(self, operator):
        response = BirdbrainRequest.response("hummingbird", "in", operator, "static", self.device)

        return (response == 'true')

    def is_microbit(self):
        """Determine if the device is a Microbit"""

        # allow hummingbird/finch to be seen as microbit
        #return self.__is_device("isMicrobit")
        return True

    def is_hummingbird(self):
        """Determine if the device is a hummingbird."""
        return self.__is_device("isHummingbird")

    def is_finch(self):
        """Determine if the device is a Finch"""

        return self.__is_device("isFinch")

    def remap_device(device):
        return device

    def connect_device(self):
        self.connected = BirdbrainRequest.is_connected(self.device)

        return self.connected

    def stop_all(self):
        BirdbrainRequest.stop_all(self.device)

    def set_cache(self, name, value):
        return self.state.set(name, value)

    def get_cache(self, name):
        return self.state.get(name)

    isConnectionValid = is_connected
    isFinch = is_finch
    isHummingbird = is_hummingbird
    isMicrobit = is_microbit
