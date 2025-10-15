from birdbrain_utility import BirdbrainUtility

def test_is_none_or_empty():
    assert BirdbrainUtility.is_none_or_empty(None)
    assert BirdbrainUtility.is_none_or_empty('')
    assert not BirdbrainUtility.is_none_or_empty('something')

def test_bounds():
    assert BirdbrainUtility.bounds(10, 0, 100) == 10
    assert BirdbrainUtility.bounds(10, -100, 100) == 10
    assert BirdbrainUtility.bounds(-10, -100, 100) == -10
    assert BirdbrainUtility.bounds(-100, -100, 100) == -100
    assert BirdbrainUtility.bounds(100, -100, 100) == 100

    assert BirdbrainUtility.bounds(101, -100, 100) == 100
    assert BirdbrainUtility.bounds(-101, -100, 100) == -100
    assert BirdbrainUtility.bounds(999999, -100, 100) == 100
    assert BirdbrainUtility.bounds(-999999, -100, 100) == -100

    assert BirdbrainUtility.bounds(str(10), str(0), str(100)) == 10
    assert BirdbrainUtility.bounds(str(10), str(-100), str(100)) == 10
    assert BirdbrainUtility.bounds(str(-10), str(-100), str(100)) == -10
    assert BirdbrainUtility.bounds(str(-100), str(-100), str(100)) == -100
    assert BirdbrainUtility.bounds(str(100), str(-100), str(100)) == 100

    assert BirdbrainUtility.bounds(str(101), str(-100), str(100)) == 100
    assert BirdbrainUtility.bounds(str(-101), str(-100), str(100)) == -100
    assert BirdbrainUtility.bounds(str(999999), str(-100), str(100)) == 100
    assert BirdbrainUtility.bounds(str(-999999), str(-100), str(100)) == -100

def test_flatten():
    flattened = BirdbrainUtility.flatten_string([ "something", "1", [ "A", "B" ], "2", "else", 99, [ 99 ]])

    assert flattened == "something/1/A/B/2/else/99/99"

def test_flatten_tuple():
    flattened = BirdbrainUtility.flatten_string( ("something", "1", [ "A", "B" ], "2", "else", 99, [ 99 ]) )

    assert flattened == "something/1/A/B/2/else/99/99"

