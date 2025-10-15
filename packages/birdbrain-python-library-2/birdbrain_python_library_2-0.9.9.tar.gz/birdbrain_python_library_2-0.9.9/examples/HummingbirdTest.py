import time

from birdbrain_hummingbird import BirdbrainHummingbird

myBird = Hummingbird('A')

for i in range(0, 10):
    myBird.setLED(1, 100)
    time.sleep(0.1)
    myBird.setLED(1, 0)
    time.sleep(0.1)

myBird.stopAll()
