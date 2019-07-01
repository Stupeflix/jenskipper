from jenskipper.cli import delete


def test_delete(requests_mock):
    requests_mock.post('/job/default_job/doDelete')
    delete.delete(['default_job', '--no-confirm'], standalone_mode=False)
