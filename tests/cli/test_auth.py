from jenskipper.cli import auth


def test_auth(requests_mock):
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.get('/')
    assert auth.authenticate([], standalone_mode=False) is None


def test_auth_with_crumbs(requests_mock):
    requests_mock.get('/')
    requests_mock.get('/api/json', json={'useCrumbs': True})
    requests_mock.get('/crumbIssuer/api/json',
                      json={'crumbRequestField': 'jenkins-crumbs',
                            'crumb': 'foofoosecret'})
    assert auth.authenticate([], standalone_mode=False) is None
