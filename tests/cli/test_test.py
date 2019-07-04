import re

from jenskipper.cli import test


def test_test(requests_mock):
    name_pattern = r'default_job%s\.[0-9a-f]{8}' % test.TEMP_JOBS_INFIX
    requests_mock.post(re.compile('/job/%s/config.xml' % name_pattern))
    queue_path = '/queue/default_job'
    requests_mock.post(
        re.compile('/job/%s/build' % name_pattern),
        status_code=201,
        headers={'location': queue_path}
    )
    build_url = '/build/default_job'
    requests_mock.get(queue_path + '/api/json',
                      json={'executable': {'url': build_url}})
    requests_mock.get(build_url + '/api/json', json={'result': 'SUCCESS'})
    requests_mock.post(re.compile('/job/%s/disable' % name_pattern))
    requests_mock.post(re.compile('/job/%s/doDelete' % name_pattern))
    exit_code = test.test(['default_job'], standalone_mode=False)
    assert exit_code is None
