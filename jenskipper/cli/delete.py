import click
import requests

from . import decorators
from .. import jenkins_api


RESULT_COLORS = {
    'SUCCESS': 'green',
    'UNSTABLE': 'yellow',
    'FAILURE': 'red',
}


@click.command()
@click.option('--confirm/--no-confirm', default=True, help='Ask for '
              'confirmation before deleting jobs (default is to ask).')
@decorators.repos_command
@decorators.jobs_command(dirty_flag=True, default_to_all=False)
@decorators.handle_all_errors()
@click.pass_context
def delete(context, jobs_names, base_dir, confirm):
    """
    Delete jobs on the Jenkins server.
    """
    session = jenkins_api.auth(base_dir)
    if confirm and jobs_names:
        question = click.style(click.wrap_text(
            'Are you sure you want to delete the following jobs on the '
            'Jenkins server?'
        ), fg='red', bold=True)
        jobs_list = '\n'.join('  %s' % n for n in jobs_names)
        click.confirm('%s\n\n%s\n\n' % (question, jobs_list), abort=True)

    exit_code = 0
    for name in jobs_names:
        try:
            jenkins_api.delete_job(session, name)
        except requests.HTTPError as exc:
            if exc.response.status_code == 404:
                click.secho('%s was not found' % name, fg='red')
                exit_code = 5

    context.exit(exit_code)
