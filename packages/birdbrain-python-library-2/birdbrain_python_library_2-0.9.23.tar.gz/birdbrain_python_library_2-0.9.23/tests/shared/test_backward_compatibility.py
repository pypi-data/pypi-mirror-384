from birdbrain_finch import BirdbrainFinch
from birdbrain_hummingbird import BirdbrainHummingbird

from BirdBrain import Finch, Hummingbird


def test_instantiating_devices_old_way():
    BirdbrainFinch('B')
    BirdbrainHummingbird('A')

    Finch('B')
    Hummingbird('A')
