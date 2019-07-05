import os

import pytest

from jenskipper import jenkins_api
from jenskipper import exceptions


def test_list_jobs(requests_mock, data_dir):
    requests_mock.get('/api/json', text=data_dir.join('api_json.json').read())
    session = jenkins_api.auth(os.environ['JK_DIR'])
    jobs = jenkins_api.list_jobs(session)
    assert jobs == ['test-project-for-jenskipper']


def test_push_job_config_type_mismatch(requests_mock, data_dir):
    requests_mock.get('/api/json', json={'useCrumbs': False})
    session = jenkins_api.auth(os.environ['JK_DIR'])
    body = data_dir.join('push_job_conf_type_error.html').read_text('utf8')
    requests_mock.post('/job/job_name/config.xml', text=body, status_code=500)
    with pytest.raises(exceptions.JobTypeMismatch) as excinfo:
        jenkins_api.push_job_config(session, 'job_name', '')
    exc = excinfo.value
    assert exc.pushed_type == 'hudson.matrix.MatrixProject'
    assert exc.expected_type == 'hudson.model.FreeStyleProject'
