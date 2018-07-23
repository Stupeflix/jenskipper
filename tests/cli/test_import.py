# -*- coding: utf8 -*-
from jenskipper.cli import import_
from jenskipper import utils
from ..utils import serve_file


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


def test_write_jobs_templates(httpserver, data_dir, tmp_dir):
    repos_dir = tmp_dir.join('repos')
    data_dir.join('repos').copy(repos_dir)
    job_config = serve_file(httpserver, data_dir.join('job_config.xml'))
    pipe_bits, jobs_templates = import_.write_jobs_templates(str(repos_dir),
                                                             httpserver.url,
                                                             ['€'])
    assert pipe_bits == {'€': (['stupeflix'], 'SUCCESS')}
    template_path = repos_dir.join('templates', '€.xml')
    assert jobs_templates == {'€': template_path}
    assert template_path.read_text('utf8') == utils.unescape_xml(job_config)
