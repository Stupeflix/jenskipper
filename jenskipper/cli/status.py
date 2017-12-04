import click
import requests
import sys

from . import decorators
from .. import jenkins_api
from .. import conf
from .. import utils


JOB_STATUS = (
    ('lastStableBuild', 'Last stable: %s', 'stable'),
    ('lastFailedBuild', 'Last failed: %s', 'failed'),
    ('lastUnstableBuild', 'Last unstable: %s', 'unstable'),
)


@click.command('status')
@click.option('--status-only', '-s', is_flag=True,
              help='Only show job names and statuses.')
@decorators.repos_command
@decorators.jobs_command()
@decorators.handle_all_errors()
def get_job_status(base_dir, jobs_names, status_only):
    """
    Retrieve the status of a job.
    """
    jenkins_url = conf.get(base_dir, ['server', 'location'])
    show_job_name = (len(jobs_names) > 1)
    for job_num, job_name in enumerate(jobs_names):
        if job_num and not status_only:
            print
        jenkins_url = _print_job_status(base_dir, jenkins_url, job_name,
                                        status_only, show_job_name)


def _print_job_status(base_dir, jenkins_url, job_name, status_only,
                      show_job_name):
    try:
        job_data, jenkins_url = jenkins_api.handle_auth(base_dir,
                                                        jenkins_api.get_object,
                                                        jenkins_url,
                                                        '/job/%s' % job_name)
    except requests.HTTPError as exc:
        if exc.response.status_code == 404:
            utils.sechowrap('Unkown job: %s' % job_name)
            exit_code = 2
        else:
            utils.sechowrap('Unexpected HTTP error %s while trying to '
                            'retrieve job data' % exc.response.status_code,
                            fg='red')
            exit_code = 1
        sys.exit(exit_code)

    status = _job_status(job_data)
    if status_only:
        print "%s: %s" % (job_name, status)
    else:
        if show_job_name:
            lines_prefix = '  '
            click.secho(job_name, fg='yellow', bold=True)
        else:
            lines_prefix = ''
        print '%sStatus: %s' % (lines_prefix, status)
        if status is 'never built':
            sys.exit(0)

        print '%sLast completed: %s' % (
            lines_prefix,
            job_data['lastCompletedBuild']['number']
        )
        for key, fmt, _ in JOB_STATUS:
            build_data = job_data[key]
            if build_data is not None:
                job_number = build_data['number']
            else:
                job_number = 'none'
            print lines_prefix + fmt % job_number

    return jenkins_url


def _job_status(job_data):
    if job_data['lastCompletedBuild'] is None:
        return 'never built'
    last_completed = job_data['lastCompletedBuild']['number']
    for key, _, status in JOB_STATUS:
        build_data = job_data[key]
        if build_data is not None and build_data['number'] == last_completed:
            return status
    return 'unknown'
