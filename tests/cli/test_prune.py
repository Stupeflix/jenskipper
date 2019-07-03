from jenskipper.cli import prune


def test_prune(requests_mock):
    requests_mock.get('/api/json', json={'jobs': [{'name': 'foo'}]})
    requests_mock.post('/job/foo/doDelete')
    prune.prune(['--no-confirm'], standalone_mode=False)


def test_nothing_to_prune(requests_mock):
    requests_mock.get('/api/json', json={'jobs': []})
    requests_mock.post('/job/foo/doDelete')
    prune.prune(['--no-confirm'], standalone_mode=False)
