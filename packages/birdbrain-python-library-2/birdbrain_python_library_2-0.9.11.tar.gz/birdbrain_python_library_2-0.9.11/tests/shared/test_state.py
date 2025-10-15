from birdbrain_state import BirdbrainState

def test_state():
    state = BirdbrainState()

    for pixel in state.display_map:
        assert pixel == 0

    assert state.display_map[0] == 0
    assert state.display_map[18] == 0

    state.set_pixel(1, 1, 1)
    state.set_pixel(4, 4, 1)
    
    assert state.display_map[0] == 1
    assert state.display_map[18] == 1
    assert state.display_map[1] == 0
    assert state.display_map[19] == 0

    s = state.display_map_normalize()

    assert s[0] == "true"
    assert s[18] == "true"
    assert s[1] == "false"
    assert s[19] == "false"

    assert state.display_map_as_string() == "true/false/false/false/false/false/false/false/false/false/false/false/false/false/false/false/false/false/true/false/false/false/false/false/false"

def test_display_map_as_string_with_list():
    state = BirdbrainState()

    list = [ 0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0 ]

    assert state.display_map_as_string(list)[0:11] == "false/true/"

def test_state_using_true_and_false():
    state = BirdbrainState()

    state.set_pixel(1, 1, False)
    state.set_pixel(4, 4, True)

    s = state.display_map_normalize()

    assert s[0] == "false"
    assert s[18] == "true"

def test_cache():
    state = BirdbrainState()

    assert state.get("something_name") == None

    assert state.set("something_name", "something") == "something"
    assert state.get("something_name") == "something"

    assert "something_name" in state.cache

    assert state.set("something_name", None) == None

    assert "something_name" not in state.cache

    assert state.get("something_name") == None

    assert state.set("set_not_in_the_cache", None) == None