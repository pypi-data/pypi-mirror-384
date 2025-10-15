class BirdbrainException(Exception):
    def __init__(self, message, birdbrain_device = None):
        if birdbrain_device is not None: birdbrain_device.stop_all()

        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message
