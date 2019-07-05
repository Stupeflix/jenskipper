# -*- coding: utf8 -*-
import os

from jenskipper.cli import import_
from jenskipper import utils
from jenskipper import jenkins_api


def test_import(requests_mock, tmp_dir):
    requests_mock.get('/api/json', json={'jobs': [{'name': 'new_job'}],
                                         'useCrumbs': False})
    job_xml = '<xml>foo</xml>'
    requests_mock.get('/job/new_job/config.xml', text=job_xml)
    repos_dir = tmp_dir.join('repos')
    ret = import_.import_(['http://test.jenskipper.com', str(repos_dir)],
                          standalone_mode=False)
    assert ret is None
    assert repos_dir.join('templates', 'new_job.xml').read() == job_xml


def test_import_repos_dir_exists(requests_mock, tmp_dir):
    requests_mock.get('/api/json', json={'useCrumbs': False})
    repos_dir = tmp_dir.join('repos')
    repos_dir.ensure(dir=True)
    exit_code = import_.import_(['http://test.jenskipper.com', str(repos_dir)],
                                standalone_mode=False)
    assert exit_code == 1


def test_write_jobs_templates_with_unicode_names(requests_mock, data_dir,
                                                 tmp_dir):
    requests_mock.get('/api/json', json={'useCrumbs': False})
    session = jenkins_api.auth(os.environ['JK_DIR'])
    repos_dir = tmp_dir.join('repos')
    data_dir.join('repos').copy(repos_dir)
    job_config = data_dir.join('job_config.xml').read_text('utf8')
    requests_mock.get('/job/%E2%82%AC/config.xml', text=job_config)
    pipe_bits, jobs_templates = import_.write_jobs_templates(session,
                                                             str(repos_dir),
                                                             ['€'])
    assert pipe_bits == {'€': (['stupeflix'], 'SUCCESS')}
    template_path = repos_dir.join('templates', '€.xml')
    assert jobs_templates == {'€': template_path}
    assert template_path.read_text('utf8') == utils.unescape_xml(job_config)
