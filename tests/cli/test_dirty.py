import shutil
import subprocess

from jenskipper.cli import dirty
from jenskipper import utils


def test_dirty_git(data_dir, tmp_dir):
    repos_dir = tmp_dir.join('repos')
    shutil.copytree(str(data_dir.join('repos')), str(repos_dir))
    with utils.cd(str(repos_dir)):
        subprocess.check_call(['git', 'init'])
        subprocess.check_call(['git', 'add', '.'])
        subprocess.check_call(['git', 'commit', '-m', 'first commit'])
    assert dirty.get_dirty_jobs(str(repos_dir), ['basic']) == set()
    with open(str(repos_dir.join('templates', 'basic.txt')), 'a') as fp:
        fp.write('bar')
    assert dirty.get_dirty_jobs(str(repos_dir), ['basic']) == {'basic'}
