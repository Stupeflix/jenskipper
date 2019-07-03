from click.testing import CliRunner

from jenskipper.cli import list_jobs


def test_list_jobs(requests_mock):
    runner = CliRunner()
    result = runner.invoke(list_jobs.list_jobs)
    assert result.exit_code == 0
    assert set(result.output.splitlines()) == {'default_job',
                                               'missing_template',
                                               'syntax_error',
                                               'undefined_var'}
