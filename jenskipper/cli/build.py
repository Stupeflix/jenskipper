import time

import requests
import click

from . import decorators
from .. import jenkins_api
from .. import utils


RESULT_COLORS = {
    'SUCCESS': 'green',
    'UNSTABLE': 'yellow',
    'FAILURE': 'red',
}


@click.command()
@click.option('--block/--no-block', default=False, help='Block until builds '
              'are done and show their outcome.')
@decorators.build_command
@decorators.repos_command
@decorators.jobs_command(dirty_flag=True)
@decorators.handle_all_errors()
@click.pass_context
def build(context, jobs_names, base_dir, block, build_parameters):
    """
    Trigger builds for JOBS.
    """
    session = jenkins_api.auth(base_dir)
    exit_code = do_build(session, jobs_names, base_dir, block,
                         build_parameters)
    context.exit(exit_code)


def do_build(session, jobs_names, base_dir, block, build_parameters):
    queue_urls = trigger_builds(session, jobs_names, base_dir,
                                build_parameters)
    exit_code = 0
    if block:
        results = wait_for_builds(session, queue_urls)
        for job_name, (build_url, result, runs_urls) in results.items():
            print_build_result(session, base_dir, job_name, build_url, result,
                               runs_urls)
        if any(r[1] != 'SUCCESS' for r in results.values()):
            exit_code = 1
    return exit_code


def trigger_builds(session, jobs_names, base_dir, parameters):
    """
    Trigger builds for *jobs_names*.

    Return a *queue_urls*, which can be passed to :func:`wait_for_builds` to
    wait for jobs completion.
    """
    queue_urls = {}
    for name in jobs_names:
        queue_url = jenkins_api.build_job(session, name, parameters)
        queue_urls[name] = queue_url
    return queue_urls


def wait_for_builds(session, queue_urls):
    """
    Wait until builds corresponding to *queue_urls* are done.

    Return a dict indexed by job names, containing ``(build_url, result,
    runs_urls)`` tuples.

    *build_url* is the location of the build, e.g.
    "http://jenkins.example.com/job/myjob/51", and *result* a string
    representing the build result ("SUCCESS", "UNSTABLE" or "FAILURE").
    *runs_urls* is a (possibly empty) list of sub runs URLs for multi
    configuration projects.
    """
    builds_urls = _get_builds_urls(session, queue_urls)
    return _poll_builds(session, builds_urls)


def print_build_result(session, base_dir, job_name, build_url, result=None,
                       runs_urls=None, prefix='', suffix='',
                       only_log_failures=True):
    """
    Print build results of a job.
    """
    # Get result and/or runs URLs if not given in arguments
    if result is None or runs_urls is None:
        build_infos = jenkins_api.get_object(session, build_url)
    if result is None:
        result = build_infos['result']
    if runs_urls is None:
        runs_urls = _get_runs_urls(build_infos)

    # A null result means the build is in progress
    if result is None:
        click.secho('%s%s: build is in progress%s' %
                    (prefix, job_name, suffix), fg='yellow')

    # Print results
    color = RESULT_COLORS[result]
    click.secho('%s%s: %s%s' % (prefix, job_name, result.lower(), suffix),
                fg=color)
    if not only_log_failures or result != 'SUCCESS':
        if not runs_urls:
            log = jenkins_api.get_build_log(session, build_url)
            _print_marker('Beginning of "%s" logs' % job_name)
            print(log.rstrip())
            _print_marker('End of "%s" logs' % job_name)
        for run_url in runs_urls:
            run_info = jenkins_api.get_object(session, run_url)
            print_build_result(session,
                               base_dir,
                               run_info['fullDisplayName'],
                               run_url,
                               run_info['result'],
                               [],
                               prefix='    ',
                               only_log_failures=only_log_failures)


def _print_marker(text, marker='-', width=79):
    print(marker * width)
    print(text.center(width))
    print(marker * width)


def _get_builds_urls(session, queue_urls):
    ret = {}
    queue_urls = queue_urls.copy()
    while True:
        for job_name, queue_url in list(queue_urls.items()):
            try:
                queue_infos = jenkins_api.get_object(session, queue_url)
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
        if not queue_urls:
            break
        time.sleep(1)
    return ret


def _poll_builds(session, builds_urls):
    ret = {}
    builds_urls = builds_urls.copy()
    while True:
        for job_name, build_url in list(builds_urls.items()):
            build_infos = jenkins_api.get_object(session, build_url)
            result = build_infos['result']
            if result is not None:
                runs_urls = _get_runs_urls(build_infos)
                ret[job_name] = (build_url, result, runs_urls)
                del builds_urls[job_name]
        if not builds_urls:
            break
        time.sleep(1)
    return ret


def _get_runs_urls(build_infos):
    if 'runs' in build_infos:
        return [r['url'] for r in build_infos['runs']]
    else:
        return []
