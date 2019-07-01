from jenskipper.cli import auth


def test_auth(requests_mock):
    requests_mock.get('/')
    auth.authenticate([], standalone_mode=False)
