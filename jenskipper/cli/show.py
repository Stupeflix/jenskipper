import click

from . import decorators
from .. import repository


@click.command()
@click.argument('job_name')
@decorators.repos_command
@decorators.context_command
@decorators.handle_all_errors()
def show(job_name, base_dir, context_overrides):
    """
    Show the rendered XML of JOB_NAME.
    """
    print(repository.get_job_conf(base_dir, job_name,
                                  context_overrides=context_overrides)[0])
