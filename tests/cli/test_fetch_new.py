import os.path as op

import pytest
import yaml

from jenskipper.cli import fetch_new


HERE = op.dirname(__file__)


@pytest.mark.parametrize('setup_cli_env_vars', [op.join(HERE, 'tmp')],
                         indirect=True)
def test_fetch_new(requests_mock, data_dir, tmp_dir, setup_cli_env_vars):
    # Copy reopsitory and user conf to tmp dir, because fetch_new is going to
    # create files in the repository
    data_dir.copy(tmp_dir)

    job_xml_1 = '<xml>new_job_1</xml>'
    job_xml_2 = '<xml>new_job_2</xml>'
    requests_mock.get('/api/json', json={'jobs': [{'name': 'new_job_1'},
                                                  {'name': 'new_job_2'}]})
    requests_mock.get('/job/new_job_1/config.xml', text=job_xml_1)
    requests_mock.get('/job/new_job_2/config.xml', text=job_xml_2)
    ret = fetch_new.fetch_new([], standalone_mode=False)
    assert ret is None
    disk_job_xml_1 = tmp_dir.join('repos', 'templates', 'new_job_1.xml').read()
    disk_job_xml_2 = tmp_dir.join('repos', 'templates', 'new_job_2.xml').read()
    assert disk_job_xml_1 == job_xml_1
    assert disk_job_xml_2 == job_xml_2
    with tmp_dir.join('repos', 'jobs.yaml').open() as fp:
        jobs = yaml.safe_load(fp)
        assert jobs['new_job_1'] == {'template': 'new_job_1.xml'}
        assert jobs['new_job_2'] == {'template': 'new_job_2.xml'}


@pytest.mark.parametrize('setup_cli_env_vars', [op.join(HERE, 'tmp')],
                         indirect=True)
def test_fetch_new_select_job(requests_mock, data_dir, tmp_dir,
                              setup_cli_env_vars):
    # Copy reopsitory and user conf to tmp dir, because fetch_new is going to
    # create files in the repository
    data_dir.copy(tmp_dir)

    job_xml_1 = '<xml>new_job_1</xml>'
    job_xml_2 = '<xml>new_job_2</xml>'
    requests_mock.get('/api/json', json={'jobs': [{'name': 'new_job_1'},
                                                  {'name': 'new_job_2'}]})
    requests_mock.get('/job/new_job_1/config.xml', text=job_xml_1)
    requests_mock.get('/job/new_job_2/config.xml', text=job_xml_2)
    ret = fetch_new.fetch_new(['new_job_1'], standalone_mode=False)
    assert ret is None
    disk_job_xml_1 = tmp_dir.join('repos', 'templates', 'new_job_1.xml').read()
    assert disk_job_xml_1 == job_xml_1
    assert not tmp_dir.join('repos', 'templates', 'new_job_2.xml').exists()


@pytest.mark.parametrize('setup_cli_env_vars', [op.join(HERE, 'tmp')],
                         indirect=True)
def test_fetch_new_select_unknown_job(requests_mock, data_dir, tmp_dir,
                                      setup_cli_env_vars):
    # Copy reopsitory and user conf to tmp dir, because fetch_new is going to
    # create files in the repository
    data_dir.copy(tmp_dir)

    requests_mock.get('/api/json', json={'jobs': [{'name': 'new_job_1'}]})
    assert fetch_new.fetch_new(['new_job_2'], standalone_mode=False) == 2


@pytest.mark.parametrize('setup_cli_env_vars', [op.join(HERE, 'tmp')],
                         indirect=True)
def test_fetch_new_overwrite_error(requests_mock, data_dir, tmp_dir,
                                   setup_cli_env_vars):
    # Copy reopsitory and user conf to tmp dir, because fetch_new is going to
    # create files in the repository
    data_dir.copy(tmp_dir)

    job_xml_1 = '<xml>new_job_1</xml>'
    requests_mock.get('/api/json', json={'jobs': [{'name': 'new_job_1'}]})
    requests_mock.get('/job/new_job_1/config.xml', text=job_xml_1)
    template = tmp_dir.join('repos', 'templates', 'new_job_1.xml')
    template.write('foo')
    assert fetch_new.fetch_new([], standalone_mode=False) == 2
    template.read() == 'foo'


@pytest.mark.parametrize('setup_cli_env_vars', [op.join(HERE, 'tmp')],
                         indirect=True)
def test_fetch_new_force_overwrite(requests_mock, data_dir, tmp_dir,
                                   setup_cli_env_vars):
    # Copy reopsitory and user conf to tmp dir, because fetch_new is going to
    # create files in the repository
    data_dir.copy(tmp_dir)

    job_xml_1 = '<xml>new_job_1</xml>'
    requests_mock.get('/api/json', json={'jobs': [{'name': 'new_job_1'}]})
    requests_mock.get('/job/new_job_1/config.xml', text=job_xml_1)
    template = tmp_dir.join('repos', 'templates', 'new_job_1.xml')
    template.write('foo')
    assert fetch_new.fetch_new(['--force'], standalone_mode=False) is None
    template.read() == job_xml_1
