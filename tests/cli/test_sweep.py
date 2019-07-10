import os.path as op

import pytest
from click.testing import CliRunner

from jenskipper.cli import sweep


HERE = op.dirname(__file__)


@pytest.mark.parametrize('setup_cli_env_vars',
                         [(op.join(HERE, 'data'), 'good-repos')],
                         indirect=True)
def test_sweep(setup_cli_env_vars):
    with setup_cli_env_vars['JK_DIR'].as_cwd():
        runner = CliRunner()
        result = runner.invoke(sweep.sweep, [])
    assert result.exit_code == 0
    assert result.output == 'templates/unused_template.txt\n'


@pytest.mark.parametrize('setup_cli_env_vars',
                         [(op.join(HERE, 'tmp'), 'good-repos')],
                         indirect=True)
def test_sweep_delete(data_dir, tmp_dir, setup_cli_env_vars):
    # Copy reopsitory and user conf to tmp dir, because sweep is going to
    # remove files in the repository
    data_dir.copy(tmp_dir)

    templates_dir = tmp_dir.join('good-repos', 'templates')
    assert 'unused_template.txt' in (p.basename
                                     for p in templates_dir.listdir())
    exit_code = sweep.sweep(['--delete'], standalone_mode=False)
    assert exit_code is None
    assert 'unused_template.txt' not in (p.basename
                                         for p in templates_dir.listdir())
