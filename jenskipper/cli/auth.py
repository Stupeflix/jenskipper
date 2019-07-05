import click

from .. import jenkins_api
from . import decorators


@click.command('auth')
@decorators.repos_command
def authenticate(base_dir):
    """
    Authenticate against the jenkins server.
    """
    jenkins_api.auth(base_dir)
