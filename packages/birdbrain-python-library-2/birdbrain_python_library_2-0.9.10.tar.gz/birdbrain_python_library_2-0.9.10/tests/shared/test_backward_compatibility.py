from birdbrain_finch import BirdbrainFinch
from birdbrain_hummingbird import BirdbrainHummingbird
from birdbrain_microbit import BirdbrainMicrobit

from BirdBrain import Finch,Hummingbird

def test_instantiating_devices_old_way():
    finch = BirdbrainFinch('B')
    hummingbird = BirdbrainHummingbird('A')

    finch = Finch('B')
    hummingbird = Hummingbird('A')
