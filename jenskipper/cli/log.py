import click

from . import build
from . import decorators
from .. import jenkins_api


@click.command()
@click.option('--build', '-b', 'build_number', type=int, help='Build number '
              '(default: last build).')
@click.option('--all', '-a', 'show_all', is_flag=True,
              help='Show all logs (default is to show only failures).')
@decorators.repos_command
@decorators.jobs_command(dirty_flag=True)
@decorators.handle_all_errors()
def log(jobs_names, base_dir, build_number, show_all):
    """
    Show logs of JOBS.

    If no JOBS are specified, show logs of all jobs.
    """
    session = jenkins_api.auth(base_dir)
    for job_name in jobs_names:
        builds = _get_job_builds(session, base_dir, job_name)
        if builds:
            if build_number is not None:
                build_url, real_build_number = _search_build_url(builds,
                                                                 build_number)
            else:
                build_url = builds[0]['url']
                real_build_number = builds[0]['number']
            if build_url is not None:
                job_name_with_build = '%s #%s' % (job_name, real_build_number)
                build.print_build_result(
                    session,
                    base_dir,
                    job_name_with_build,
                    build_url,
                    only_log_failures=not show_all,
                )
            else:
                click.secho('%s: build #%s does not exist' % (job_name,
                                                              build_number))
        else:
            click.secho('%s: no builds' % job_name, fg='yellow')


def _get_job_builds(session, base_dir, job_name):
    path = '/job/%s' % job_name
    job_infos = jenkins_api.get_object(session, path)
    return job_infos['builds']


def _search_build_url(builds, build_number):
    for build_info in builds:
        if build_number == build_info['number']:
            return build_info['url'], build_info['number']
