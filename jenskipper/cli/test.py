import uuid

import click

from . import decorators
from . import build
from .. import jenkins_api
from .. import repository


TEMP_JOBS_INFIX = '.JK_TEST'


@click.command()
@decorators.build_command
@decorators.repos_command
@decorators.jobs_command(dirty_flag=True)
@decorators.context_command
@decorators.handle_all_errors()
def test(jobs_names, base_dir, context_overrides, build_parameters):
    """
    Create temporary copies of JOBS and execute them.

    This command blocks until all jobs are done. Jobs that succeeded are
    deleted, and failures are kept for inspection.
    """
    session = jenkins_api.auth(base_dir)
    new_jobs_names = _create_temp_jobs(session, jobs_names, base_dir,
                                       context_overrides)
    queue_urls = build.trigger_builds(session,
                                      new_jobs_names,
                                      base_dir,
                                      build_parameters)
    results = build.wait_for_builds(session, queue_urls)
    _disable_jobs(session, base_dir, new_jobs_names)
    _process_results(session, base_dir, results)


def _create_temp_jobs(session, jobs_names, base_dir, context_overrides):
    ret = []
    for job_name in jobs_names:
        temp_name = '%s%s.%s' % (job_name, TEMP_JOBS_INFIX,
                                 uuid.uuid4().hex[:8])
        conf, _ = repository.get_job_conf(base_dir, job_name,
                                          context_overrides=context_overrides)
        jenkins_api.push_job_config(session, temp_name, conf)
        ret.append(temp_name)
    return ret


def _process_results(session, base_dir, results):
    for job_name, (build_url, result, runs_urls) in results.items():
        orig_job_name, _, _ = job_name \
                              .replace(TEMP_JOBS_INFIX, '') \
                              .rpartition('.')
        if result == 'SUCCESS':
            jenkins_api.delete_job(session, job_name)
            suffix = ''
        else:
            suffix = ', see %s' % build_url
        build.print_build_result(session, base_dir, orig_job_name, build_url,
                                 result, runs_urls, suffix=suffix)


def _disable_jobs(session, base_dir, jobs_names):
    for job_name in jobs_names:
        jenkins_api.toggle_job(session, job_name, False)
