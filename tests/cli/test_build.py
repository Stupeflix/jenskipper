from jenskipper.cli import build


def test_build(requests_mock):
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.post(
        '/job/default_job/build',
        status_code=201,
        headers={'location': '/queue/default_job'}
    )
    ret = build.build(['default_job', '--no-block'], standalone_mode=False)
    assert ret == 0


def test_build_block(requests_mock):
    requests_mock.get('/api/json', json={'useCrumbs': False})
    queue_path = '/queue/default_job'
    requests_mock.post(
        '/job/default_job/build',
        status_code=201,
        headers={'location': queue_path}
    )
    build_url = '/build/default_job'
    requests_mock.get(queue_path + '/api/json',
                      json={'executable': {'url': build_url}})
    requests_mock.get(build_url + '/api/json', json={'result': 'SUCCESS'})
    ret = build.build(['default_job', '--block'], standalone_mode=False)
    assert ret == 0
