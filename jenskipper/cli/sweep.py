import os
import os.path as op

import click

from . import decorators
from .. import repository
from .. import jobs


@click.command()
@click.option('--delete/--no-delete', default=False, help='Delete '
              'unused templates.')
@decorators.repos_command
@decorators.handle_all_errors()
def sweep(base_dir, delete):
    """
    Find unused templates in the current repository.
    """
    templates_dir = repository.get_templates_dir(base_dir)

    # Get all files used by templates
    jobs_defs = repository.get_jobs_defs(base_dir)
    pipelines = repository.get_pipelines(base_dir)
    used_files = set()
    for job_name, job_def in jobs_defs.items():
        pipe_info = pipelines.get(job_name)
        _, job_files = jobs.render_job(templates_dir, job_def['template'],
                                       job_def['context'], pipe_info)
        used_files.update(job_files)

    # Get all files in the templates dir
    templates_dir_files = set()
    for dirpath, dirnames, filenames in os.walk(templates_dir):
        templates_dir_files.update(op.join(dirpath, n)
                                   for n in filenames
                                   if not n.startswith('.'))

    dead_files = templates_dir_files.difference(used_files)
    print('\n'.join(op.relpath(p) for p in dead_files))

    # Optionally delete dead templates
    if delete:
        for path in dead_files:
            os.unlink(path)
