from jenskipper.cli import log


def test_log(requests_mock):
    requests_mock.get('/job/default_job/api/json',
                      json={'builds': [{'url': '/foo', 'number': 1}]})
    requests_mock.get('/foo/api/json', json={'result': 'SUCCESS'})
    requests_mock.get('/consoleText', text='log')
    ret = log.log(['default_job', '--all'], standalone_mode=False)
    assert ret is None


def test_log_with_build_number(requests_mock):
    requests_mock.get('/job/default_job/api/json',
                      json={'builds': [{'url': '/foo', 'number': 1}]})
    requests_mock.get('/foo/api/json', json={'result': 'SUCCESS'})
    requests_mock.get('/consoleText', text='log')
    ret = log.log(['default_job', '--all', '--build', '1'],
                  standalone_mode=False)
    assert ret is None
