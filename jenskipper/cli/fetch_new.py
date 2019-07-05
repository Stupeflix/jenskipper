import click

from . import decorators
from . import import_
from .. import repository
from .. import jenkins_api
from .. import exceptions
from .. import utils


@click.command('fetch-new')
@click.argument('selected_jobs', nargs=-1, metavar='JOBS')
@click.option('--force/--no-force', default=False, help='Allow overwriting '
              'existing files.')
@decorators.repos_command
@decorators.handle_all_errors()
@click.pass_context
def fetch_new(context, base_dir, force, selected_jobs):
    """
    Fetch new jobs in an existing repository.

    You can specify which jobs to fetch with JOBS. If no JOBS are specified,
    fetch all new jobs.
    """
    session = jenkins_api.auth(base_dir)
    repos_jobs = repository.get_jobs_defs(base_dir)
    server_jobs = jenkins_api.list_jobs(session)
    new_jobs = set(server_jobs).difference(repos_jobs)
    if selected_jobs:
        unknown_jobs = set(selected_jobs).difference(new_jobs)
        if unknown_jobs:
            click.secho('Unknown jobs: %s' % ', '.join(unknown_jobs))
            context.exit(2)
        new_jobs = new_jobs.intersection(selected_jobs)
    if new_jobs:
        try:
            with click.progressbar(new_jobs, label='Fetching new jobs') as bar:
                pipes_bits, jobs_templates = import_.write_jobs_templates(
                    session,
                    base_dir,
                    bar,
                    allow_overwrite=force,
                )
        except exceptions.OverwriteError as exc:
            click.secho('File already exists: %s' % exc, fg='red',
                        bold=True)
            click.secho('Use --force to overwrite', fg='green')
            context.exit(2)
        import_.write_jobs_defs(base_dir, jobs_templates, 'a', pad_lines=1)
        import_.write_pipelines(base_dir, pipes_bits, 'a')
    utils.print_jobs_list('New jobs:', new_jobs, empty_label='No new jobs',
                          fg='green')
