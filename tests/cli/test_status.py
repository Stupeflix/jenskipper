from jenskipper.cli import status


def test_status(requests_mock):
    requests_mock.get('/job/default_job/api/json',
                      json={'lastCompletedBuild': {'number': 2},
                            'lastStableBuild': {'number': 2},
                            'lastFailedBuild': {'number': 1},
                            'lastUnstableBuild': None})
    requests_mock.get('/foo/api/json', json={'result': 'SUCCESS'})
    exit_code = status.get_job_status(['default_job'], standalone_mode=False)
    assert exit_code is None


def test_status_only(requests_mock):
    requests_mock.get('/job/default_job/api/json',
                      json={'lastCompletedBuild': {'number': 2},
                            'lastStableBuild': {'number': 2},
                            'lastFailedBuild': {'number': 1},
                            'lastUnstableBuild': None})
    requests_mock.get('/foo/api/json', json={'result': 'SUCCESS'})
    exit_code = status.get_job_status(['default_job', '--status-only'],
                                      standalone_mode=False)
    assert exit_code is None


def test_status_never_built(requests_mock):
    requests_mock.get('/job/default_job/api/json',
                      json={'lastCompletedBuild': None})
    requests_mock.get('/foo/api/json', json={'result': 'SUCCESS'})
    exit_code = status.get_job_status(['default_job'], standalone_mode=False)
    assert exit_code is None


def test_status_unknown_job(requests_mock):
    requests_mock.get('/job/default_job/api/json', status_code=404)
    exit_code = status.get_job_status(['default_job'], standalone_mode=False)
    assert exit_code == 2


def test_status_unexpected_error(requests_mock):
    requests_mock.get('/job/default_job/api/json', status_code=520)
    exit_code = status.get_job_status(['default_job'], standalone_mode=False)
    assert exit_code == 1
