from jenskipper.cli import get_artifact


def test_get_artifact(requests_mock, tmp_dir):
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.get('/job/default_job/api/json',
                      json={'lastCompletedBuild': {'number': 1}})
    requests_mock.get('/job/default_job/1/artifact/artifact', text='foo')
    artifact_path = tmp_dir.join('artifact')
    ret = get_artifact.get_artifact(['default_job', 'artifact',
                                     '--output-file', artifact_path],
                                    standalone_mode=False)
    assert ret is None
    assert artifact_path.read() == 'foo'


def test_get_artifact_not_found(requests_mock, tmp_dir):
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.get('/job/default_job/api/json',
                      json={'lastCompletedBuild': {'number': 1}})
    requests_mock.get('/job/default_job/1/artifact/artifact', status_code=404)
    artifact_path = tmp_dir.join('artifact')
    exit_code = get_artifact.get_artifact(['default_job', 'artifact',
                                           '--output-file', artifact_path],
                                          standalone_mode=False)
    assert exit_code == 1


def test_get_artifact_by_build_number(requests_mock, tmp_dir):
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.get('/job/default_job/api/json',
                      json={'lastCompletedBuild': {'number': 1}})
    requests_mock.get('/job/default_job/1/artifact/artifact', text='foo')
    artifact_path = tmp_dir.join('artifact')
    ret = get_artifact.get_artifact(['default_job', 'artifact', '--build', '1',
                                     '--output-file', artifact_path],
                                    standalone_mode=False)
    assert ret is None
    assert artifact_path.read() == 'foo'


def test_get_artifact_invalid_build_number(requests_mock, tmp_dir):
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.get('/job/default_job/api/json',
                      json={'lastCompletedBuild': {'number': 1}})
    requests_mock.get('/job/default_job/1/artifact/artifact', text='foo')
    artifact_path = tmp_dir.join('artifact')
    ret = get_artifact.get_artifact(['default_job', 'artifact', '--build',
                                     'bar', '--output-file', artifact_path],
                                    standalone_mode=False)
    assert ret == 1


def test_get_artifact_unknown_job(requests_mock, tmp_dir):
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.get('/job/default_job/api/json', status_code=404)
    ret = get_artifact.get_artifact(['default_job', 'artifact'],
                                    standalone_mode=False)
    assert ret == 1


def test_get_artifact_no_build_data(requests_mock, tmp_dir):
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.get('/job/default_job/api/json',
                      json={'lastCompletedBuild': None})
    ret = get_artifact.get_artifact(['default_job', 'artifact'],
                                    standalone_mode=False)
    assert ret == 1
