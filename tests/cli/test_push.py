import os.path as op

from click.testing import CliRunner
import pytest

from jenskipper.cli import push


HERE = op.dirname(__file__)


def test_push(requests_mock):
    server_xml = '''<xml>
  <description>
   description
   -*- jenskipper-hash: b428261dacc8daf9cd0686b3d27d67b93450ff68 -*-
  </description>
</xml>'''
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.get('/job/default_job/config.xml', text=server_xml)
    requests_mock.post('/job/default_job/config.xml')
    assert push.push(['default_job'], standalone_mode=False) is None


def test_push_new_job(requests_mock):
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.get('/job/default_job/config.xml', status_code=404)
    requests_mock.post('/job/default_job/config.xml', status_code=404)
    requests_mock.post('/createItem?name=default_job')
    assert push.push(['default_job'], standalone_mode=False) is None


def test_push_type_mismatch(requests_mock):
    server_xml = '''<xml>
  <description>
   description
   -*- jenskipper-hash: b428261dacc8daf9cd0686b3d27d67b93450ff68 -*-
  </description>
</xml>'''
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.get('/job/default_job/config.xml', text=server_xml)
    requests_mock.post('/job/default_job/config.xml', status_code=500,
                       text='java.io.IOException: Expecting class foo but '
                       'got class bar instead')
    runner = CliRunner()
    result = runner.invoke(push.push, ['default_job', '--no-confirm-replace'])
    assert result.exit_code == 1
    assert 'expected: foo' in result.output
    assert 'pushed: bar' in result.output


def test_push_job_modified_in_gui(requests_mock):
    server_xml = '''<xml>
  <description>
   description
   -*- jenskipper-hash: 00000 -*-
  </description>
</xml>'''
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.get('/job/default_job/config.xml', text=server_xml)
    requests_mock.post('/job/default_job/config.xml')
    assert push.push(['default_job'], standalone_mode=False) == 1


@pytest.mark.parametrize('setup_cli_env_vars', [op.join(HERE, 'tmp')],
                         indirect=True)
def test_push_new_job_with_disable_jobs_from_gui(requests_mock, data_dir,
                                                 tmp_dir, setup_cli_env_vars):
    data_dir.copy(tmp_dir)
    tmp_dir.join('repos', '.jenskipper.conf') \
           .write('disable_jobs_from_gui = true\n', 'at')
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.get('/job/default_job/config.xml', status_code=404)
    requests_mock.post('/job/default_job/config.xml', status_code=404)
    requests_mock.post('/createItem?name=default_job')
    assert push.push(['default_job'], standalone_mode=False) is None
