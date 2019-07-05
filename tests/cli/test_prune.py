from jenskipper.cli import prune


def test_prune(requests_mock):
    requests_mock.get('/api/json', json={'jobs': [{'name': 'foo'}]})
    requests_mock.post('/job/foo/doDelete')
    assert prune.prune(['--no-confirm'], standalone_mode=False) is None


def test_nothing_to_prune(requests_mock):
    requests_mock.get('/api/json', json={'jobs': []})
    requests_mock.post('/job/foo/doDelete')
    assert prune.prune(['--no-confirm'], standalone_mode=False) is None
