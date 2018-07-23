import click

from . import decorators
from .. import repository


@click.command('list-jobs')
@decorators.repos_command
@decorators.handle_all_errors()
def list_jobs(base_dir):
    """
    List jobs in a repository.
    """
    jobs_defs = repository.get_jobs_defs(base_dir)
    for name in sorted(jobs_defs):
        print(name)
