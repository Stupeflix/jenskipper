import sys
import time

import requests
import click

from . import decorators
from .. import jenkins_api
from .. import conf
from .. import utils


RESULT_COLORS = {
    'SUCCESS': 'green',
    'UNSTABLE': 'yellow',
    'FAILURE': 'red',
}


@click.command()
@click.option('--block/--no-block', default=False, help='Block until builds '
              'are done and show their outcome.')
@click.option('--parameter', '-p', 'parameters', multiple=True, help='Pass a '
              'parameter to the build, in NAME=VALUE format. Use --parameter '
              'multiple times to pass multiple parameters.')
@decorators.repos_command
@decorators.jobs_command
@decorators.handle_all_errors()
def build(jobs_names, base_dir, block, parameters):
    '''
    Trigger builds for JOBS.
    '''
    jenkins_url = conf.get(base_dir, ['server', 'location'])
    queue_urls, jenkins_url = trigger_builds(jobs_names, base_dir, jenkins_url,
                                             parameters)
    if block:
        results = wait_for_builds(queue_urls, jenkins_url)
        for job_name, (build_url, result, runs_urls) in results.items():
            jenkins_url = print_build_result(base_dir, jenkins_url, job_name,
                                             build_url, result, runs_urls)
        sys.exit(any(r != 'SUCCESS' for r in results.values()))


def trigger_builds(jobs_names, base_dir, jenkins_url, parameters):
    '''
    Trigger builds for *jobs_names*.

    Return a ``(queue_urls, jenkins_url)`` tuple; *queue_urls* can be passed
    to :func:`wait_for_builds` to wait for jobs completion.
    '''
    queue_urls = {}
    for name in jobs_names:
        queue_url, jenkins_url = jenkins_api.handle_auth(
            base_dir,
            jenkins_api.build_job,
            jenkins_url,
            name,
            parameters
        )
        queue_urls[name] = queue_url
    return queue_urls, jenkins_url


def wait_for_builds(queue_urls, jenkins_url):
    '''
    Wait until builds corresponding to *queue_urls* are done.

    Return a dict indexed by job names, containing ``(build_url, result,
    runs_urls)`` tuples.

    *build_url* is the location of the build, e.g.
    "http://jenkins.example.com/job/myjob/51", and *result* a string
    representing the build result ("SUCCESS", "UNSTABLE" or "FAILURE").
    *runs_urls* is a (possibly empty) list of sub runs URLs for multi
    configuration projects.
    '''
    builds_urls = _get_builds_urls(jenkins_url, queue_urls)
    return _poll_builds(jenkins_url, builds_urls)


def print_build_result(base_dir, jenkins_url, job_name, build_url, result=None,
                       runs_urls=None, prefix='', suffix='',
                       only_log_failures=True):
    '''
    Print build results of a job.
    '''
    # Get result and/or runs URLs if not given in arguments
    if result is None or runs_urls is None:
        build_infos, jenkins_url = jenkins_api.handle_auth(
            base_dir,
            jenkins_api.get_object,
            jenkins_url,
            build_url
        )
    if result is None:
        result = build_infos['result']
    if runs_urls is None:
        runs_urls = _get_runs_urls(build_infos)

    # A null result means the build is in progress
    if result is None:
        click.secho('%s%s: build is in progress%s' %
                    (prefix, job_name, suffix), fg='yellow')
        return jenkins_url

    # Print results
    color = RESULT_COLORS[result]
    click.secho('%s%s: %s%s' % (prefix, job_name, result.lower(), suffix),
                fg=color)
    if not only_log_failures or result != 'SUCCESS':
        if not runs_urls:
            log, jenkins_url = jenkins_api.handle_auth(
                base_dir,
                jenkins_api.get_build_log,
                jenkins_url,
                build_url
            )
            print '-' * 79
            print 'Beginning of "%s" logs' % job_name.encode('utf8')
            print '-' * 79
            print log.rstrip()
            print '-' * 79
            print 'End of "%s" logs' % job_name.encode('utf8')
            print '-' * 79
        for run_url in runs_urls:
            run_info = jenkins_api.get_object(jenkins_url, run_url)
            jenkins_url = print_build_result(
                base_dir,
                jenkins_url,
                run_info['fullDisplayName'],
                run_url,
                run_info['result'],
                [],
                prefix='    ',
                only_log_failures=only_log_failures,
            )
    return jenkins_url


def _get_builds_urls(jenkins_url, queue_urls):
    _, username, password = utils.split_auth_in_url(jenkins_url)
    ret = {}
    queue_urls = queue_urls.copy()
    while queue_urls:
        for job_name, queue_url in queue_urls.items():
            try:
                queue_infos = jenkins_api.get_object(jenkins_url, queue_url)
            except requests.HTTPError as exc:
                if exc.response.status_code == 404:
                    # A 404 means that the queue info is not available anymore.
                    # We don't have any way to tell if the job was executed or
                    # not in this case, so just ignore it.
                    utils.sechowrap('%s: unknown status' % job_name,
                                    fg='yellow')
                    del queue_urls[job_name]
                else:
                    raise
            else:
                if 'executable' in queue_infos:
                    ret[job_name] = queue_infos['executable']['url']
                    del queue_urls[job_name]
        time.sleep(1)
    return ret


def _poll_builds(jenkins_url, builds_urls):
    ret = {}
    builds_urls = builds_urls.copy()
    while builds_urls:
        for job_name, build_url in builds_urls.items():
            build_infos = jenkins_api.get_object(jenkins_url, build_url)
            result = build_infos['result']
            if result is not None:
                runs_urls = _get_runs_urls(build_infos)
                ret[job_name] = (build_url, result, runs_urls)
                del builds_urls[job_name]
        time.sleep(1)
    return ret


def _get_runs_urls(build_infos):
    if 'runs' in build_infos:
        return [r['url'] for r in build_infos['runs']]
    else:
        return []
