class BirdbrainState:
    def __init__(self):
        self.cache = {}
        self.display_map = BirdbrainState.microbit_empty_display_map()

    def display_map_clear(self):
        self.display_map = BirdbrainState.microbit_empty_display_map

    def set_list(self, list):
        self.display_map = list

    def set_pixel(self, x, y, value):
        self.display_map[((x * 5) + y - 6)] = value

    def display_map_normalize(self):
        return(["true" if ((pixel == 1) or (pixel is True)) else "false" for pixel in self.display_map])

    def display_map_as_string(self, list = None):
        if list is not None: self.set_list(list)

        return "/".join(self.display_map_normalize())

    def set(self, name, value):
        if value == None:
            if name in self.cache:
                self.cache.pop(name)
        else:
            self.cache[name] = value

        return value

    def get(self, name):
        if name in self.cache:
            return self.cache[name]
        else:
            return None

    @classmethod
    def microbit_empty_display_map(self):
        return([0] * 25)
