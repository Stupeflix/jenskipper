import pytest

from jenskipper import utils


def test_set_path_in_dict():
    assert utils.set_path_in_dict({}, ['foo'], 1) == {'foo': 1}
    assert utils.set_path_in_dict({}, ['foo', 'bar'], 1) == {'foo': {'bar': 1}}
    assert utils.set_path_in_dict({'foo': {'bar': 1}}, ['foo', 'bar'], 2) == \
        {'foo': {'bar': 2}}
    with pytest.raises(TypeError):
        utils.set_path_in_dict({'foo': 1}, ['foo', 'bar'], 1)


def test_deep_merge():
    assert utils.deep_merge(
        {'a': {'b': 'c'}},
        {'a': {'b': 'C', 'D': 'E'}, 'F': 'G'}
    ) == {'a': {'b': 'C', 'D': 'E'}, 'F': 'G'}
