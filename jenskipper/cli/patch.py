import subprocess

import click

from .. import utils
from .. import exceptions
from .. import jenkins_api
from . import decorators
from . import diff


@click.command()
@decorators.repos_command
@decorators.jobs_command(num_jobs=1)
@decorators.handle_all_errors()
@click.argument('fname', type=click.Path(exists=True, dir_okay=False,
                                         writable=True))
@click.pass_context
def patch(context, jobs_names, base_dir, fname):
    """
    Try to patch FNAME with the diff between local and remote versions of a
    job.

    WARNING: this may not always work and does not take into account the Jinja
    macros. Always check your diffs before commiting changes made by this
    command.
    """
    session = jenkins_api.auth(base_dir)

    # Get diff
    job_name = jobs_names[0]
    try:
        diff_lines = diff.get_job_diff(session, base_dir, job_name, {},
                                       reverse=True)
    except exceptions.JobNotFound:
        utils.sechowrap('')
        utils.sechowrap('Unknown job: %s' % job_name, fg='red', bold=True)
        utils.sechowrap('Job is present in the local repository, but not '
                        'on the Jenkins server.', fg='red')
        context.exit(1)

    # Patch output file
    patch_proc = subprocess.Popen(['patch', '--no-backup-if-mismatch', fname],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE)
    # It's important to add a newline at the end of the patch, so patch can
    # distinguate the end of the file
    patch = ''.join(diff_lines).encode('utf8') + b'\n'
    patch_stdout, patch_stderr = patch_proc.communicate(patch)
    if patch_proc.returncode != 0:
        click.secho('Patch failed:', fg='red', bold=True)
        click.secho(patch_stdout.strip().decode('utf8'))
        click.secho(patch_stderr.strip().decode('utf8'))
        context.exit(1)
