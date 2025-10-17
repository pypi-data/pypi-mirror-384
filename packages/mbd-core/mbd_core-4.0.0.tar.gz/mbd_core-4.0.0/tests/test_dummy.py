from mbd_core.dummy import dummy_func


def test_dummy_func():
    result = 2
    assert dummy_func(1, 1) == result
