from jenskipper.cli import delete


def test_delete(requests_mock):
    requests_mock.post('/job/default_job/doDelete')
    ret = delete.delete(['default_job', '--no-confirm'], standalone_mode=False)
    assert ret == 0
