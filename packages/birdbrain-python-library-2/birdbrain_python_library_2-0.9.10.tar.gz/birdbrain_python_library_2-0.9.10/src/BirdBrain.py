# --------------------------------------------------------------
# Author                  Raghunath J, revised by Bambi Brewer
#                         and Kristina Lauwers
# Last Edit Date          11/20/2019
# Description             This python file contains Microbit,
# Hummingbird, and Finch classes.
#
# The Microbit class controls a micro:bit via bluetooth. It
# includes methods to print on the micro:bit LED array or set
# those LEDs individually. It also contains methods to read the
# values of the micro:bit accelerometer and magnetometer.
#
# The Hummingbird class extends the Microbit class to incorporate
# functions to control the inputs and outputs of the Hummingbird
# Bit. It includes methods to set the values of motors and LEDs,
# as well as methods to read the values of the sensors.
#
# The Finch class also extends the Microbit class. This class
# similarly includes function to control the inputs and outputs
# of the Finch robot.
#
# Revised 3/2025 by Frank Morton @ Base2 Incorporated
#
# This file is left for historical reasons and backward
# compatibility. Originally, all classes were in this single
# file. Now they are broken into separate files and published
# in pypi.org.
# --------------------------------------------------------------
from birdbrain_finch import BirdbrainFinch
from birdbrain_hummingbird import BirdbrainHummingbird
from birdbrain_microbit import BirdbrainMicrobit

class Microbit(BirdbrainMicrobit): pass

class Hummingbird(BirdbrainHummingbird): pass

class Finch(BirdbrainFinch): pass
