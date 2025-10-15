import time

from BirdBrain import BirdbrainFinch

myFinch = Finch('A')

for i in range(0, 10):
    myFinch.setBeak(100, 100, 100)
    time.sleep(0.1)
    myFinch.setBeak(0, 0, 0)
    time.sleep(0.1)

myFinch.stopAll()
