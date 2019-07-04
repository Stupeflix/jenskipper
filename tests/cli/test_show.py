import os

from click.testing import CliRunner

from jenskipper import repository
from jenskipper.cli import show


def test_show():
    job_config = repository.get_job_conf(os.environ['JK_DIR'],
                                         'default_job')[0]
    runner = CliRunner()
    result = runner.invoke(show.show, ['default_job'])
    assert result.exit_code == 0
    assert result.output == job_config + '\n'


def test_show_with_overrides():
    overrides = {'name': 'foo'}
    job_config = repository.get_job_conf(os.environ['JK_DIR'],
                                         'default_job',
                                         context_overrides=overrides)[0]
    runner = CliRunner()
    result = runner.invoke(show.show, ['default_job'] +
                           ['--context=%s=%s' % (k, v)
                            for k, v in overrides.items()])
    assert result.exit_code == 0
    assert result.output == job_config + '\n'
