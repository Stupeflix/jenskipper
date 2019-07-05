import click

from . import decorators
from .. import jenkins_api
from .. import repository
from .. import utils


@click.command()
@click.option('--confirm/--no-confirm', default=True, help='Ask '
              'for confirmation before deleting jobs (default is '
              'to ask).')
@decorators.repos_command
@decorators.handle_all_errors()
def prune(base_dir, confirm):
    """
    Remove all jobs on the server that are not present in the repository.
    """
    session = jenkins_api.auth(base_dir)
    repos_jobs = repository.get_jobs_defs(base_dir)
    server_jobs = jenkins_api.list_jobs(session)
    unknown_jobs = set(server_jobs).difference(repos_jobs)
    if unknown_jobs:
        _confirm_and_delete(session, base_dir, unknown_jobs, confirm)
    else:
        utils.sechowrap('Nothing to delete')


def _confirm_and_delete(session, base_dir, unknown_jobs, confirm):
    utils.sechowrap('The following jobs are present on the server but not in '
                    'the local repository:', fg='yellow')
    click.secho('  ' + '\n  '.join(sorted(unknown_jobs)), fg='yellow')
    if confirm:
        utils.sechowrap('')
        delete = click.confirm(click.style(click.wrap_text(
            'Do you really want to delete these jobs? THIS CANNOT BE '
            'RECOVERED!'
        ), fg='red', bold=True))
    else:
        delete = True
    if delete:
        for job in unknown_jobs:
            jenkins_api.delete_job(session, job)
