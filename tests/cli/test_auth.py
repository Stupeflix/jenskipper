from jenskipper.cli import auth


def test_auth(requests_mock):
    requests_mock.get('/')
    assert auth.authenticate([], standalone_mode=False) is None
