import sys

import click
import jinja2

from . import decorators
from .. import repository
from .. import templates


@click.command()
@decorators.repos_command
@decorators.jobs_command()
@click.pass_context
def check(context, jobs_names, base_dir):
    """
    Check JOBS templates render correctly.
    """
    if not jobs_names:
        context.exit(0)

    ret = 0
    for job in jobs_names:
        click.secho('Checking %s' % job, fg='green')
        try:
            repository.get_job_conf(base_dir, job)
        except jinja2.TemplateNotFound as exc:
            click.secho('    Template not found: %s' % exc.name, fg='red',
                        bold=True)
            click.secho('')
            ret |= 1
        except jinja2.TemplateError:
            exc_info = sys.exc_info()
            stack, error = templates.extract_jinja_error(exc_info, base_dir)
            templates.print_jinja_error(stack, error, lines_prefix='    ')
            click.secho('')
            ret |= 2

    click.secho('')
    if ret == 0:
        click.secho('All good!', fg='green', bold=True)
    else:
        click.secho('There were some errors :(', fg='red', bold=True)

    context.exit(ret)
