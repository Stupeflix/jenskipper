import os
from click.testing import CliRunner

from jenskipper.cli import diff
from jenskipper import repository


def test_diff(requests_mock):
    requests_mock.get('/job/default_job/config.xml', text='<xml>joob</xml>')
    assert diff.diff(['default_job'], standalone_mode=False) == 3


def test_diff_reverse(requests_mock):
    requests_mock.get('/job/default_job/config.xml', text='<xml>joob</xml>')
    assert diff.diff(['default_job', '--reverse'], standalone_mode=False) == 3


def test_no_diff(requests_mock, data_dir):
    job_config = repository.get_job_conf(os.environ['JK_DIR'],
                                         'default_job')[0]
    requests_mock.get('/job/default_job/config.xml', text=job_config)
    assert diff.diff(['default_job'], standalone_mode=False) == 0


def test_diff_job_not_found_on_server(requests_mock):
    requests_mock.get('/job/default_job/config.xml', status_code=404)
    assert diff.diff(['default_job'], standalone_mode=False) == 2


def test_diff_names_only(requests_mock):
    requests_mock.get('/job/default_job/config.xml', text='<xml>joob</xml>')
    runner = CliRunner()
    result = runner.invoke(diff.diff, ['default_job', '--names-only'])
    assert result.exit_code == 3
    assert result.output == 'default_job\n'


def test_diff_with_context_overrides(requests_mock):
    requests_mock.get('/job/default_job/config.xml', text='<xml>job</xml>')
    assert diff.diff(['default_job', '--context', 'name=joob'],
                     standalone_mode=False) == 3
