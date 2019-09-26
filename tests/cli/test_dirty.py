import subprocess

import pytest

from jenskipper.cli import dirty
from jenskipper import utils


@pytest.mark.git
def test_dirty_git(data_dir, tmp_dir):
    repos_dir = tmp_dir.join('repos')
    data_dir.join('repos').copy(repos_dir)
    with utils.cd(str(repos_dir)):
        subprocess.check_call(['git', 'init'])
        subprocess.check_call(['git', 'add', '.'])
        subprocess.check_call(['git', 'commit', '-m', 'first commit'])
    assert dirty.get_dirty_jobs(str(repos_dir), ['default_job']) == set()
    repos_dir.join('templates', 'default_job.txt').write('bar', mode='a')
    assert dirty.get_dirty_jobs(str(repos_dir), ['default_job']) == \
        {'default_job'}
