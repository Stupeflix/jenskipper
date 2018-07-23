import sys
import os
import os.path as op
import subprocess
import collections
import logging

import click
from six.moves import reduce

from . import decorators
from .. import repository


logger = logging.getLogger(__name__)


@click.command('dirty')
@decorators.repos_command
@decorators.jobs_command()
def print_dirty_jobs(jobs_names, base_dir):
    """
    Print the list of jobs with uncommitted changes in the current repository.
    """
    dirty_jobs = get_dirty_jobs(base_dir, jobs_names)
    print('\n'.join(sorted(dirty_jobs)))


def get_dirty_jobs(base_dir, jobs_names=None):
    """
    Get the list of dirty job names in the jenskipper repository at *base_dir*.

    If *jobs_names* is given, it should be a list of the jobs to examine. The
    default is to examine all jobs.
    """
    # Get the list of dirty files in the repository
    vcs = _get_vcs(base_dir)
    if vcs == 'git':
        dirty_files = _get_git_dirty_files(base_dir)
    else:
        click.secho('Unkown control version system', fg='red', bold=True)
        sys.exit(1)

    # Build a map of template files to jobs
    jobs_defs = repository.get_jobs_defs(base_dir)
    if jobs_names:
        examined_jobs = set(jobs_defs).intersection(jobs_names)
    else:
        examined_jobs = jobs_defs.keys()
    files_jobs = collections.defaultdict(set)
    for job_name in examined_jobs:
        logger.debug('looking at: %s', job_name)
        _, job_files = repository.get_job_conf(base_dir, job_name)
        for fname in job_files:
            files_jobs[fname].add(job_name)

    # Show dirty jobs
    return reduce(set.union,
                  (files_jobs[fname] for fname in dirty_files),
                  set())


def _get_vcs(base_dir):
    if '.git' in os.listdir(base_dir):
        return 'git'


def _get_git_dirty_files(base_dir):
    git_output = subprocess.check_output(
        ['git', '-C', base_dir, 'status', '--porcelain']
    )
    git_output = git_output.decode('utf8')
    ret = []
    for line in git_output.splitlines():
        fnames = line[3:].split()
        fnames = [op.join(base_dir, f) for f in fnames]
        ret.extend(fnames)
    return ret
