import click

from . import decorators
from . import diff
from . import build
from .. import repository
from .. import jobs
from .. import jenkins_api
from .. import conf
from .. import utils
from .. import exceptions


@click.command()
@click.option('--force/--no-force', default=False, help='Allow pushing, even '
              'if pushes are disabled in the configuration.')
@click.option('--allow-overwrite/--no-allow-overwrite', default=False,
              help='Allow overwriting changes made in the GUI.')
@click.option('-b', '--build', 'trigger_builds', help='Also trigger builds.',
              is_flag=True)
@click.option('--block/--no-block', 'block_builds', default=False,
              help='Block until builds are done and show their outcome.')
@click.option('--confirm-replace/--no-confirm-replace', default=True,
              help='Confirm before replacing jobs of different types.')
@decorators.repos_command
@decorators.jobs_command(dirty_flag=True)
@decorators.context_command
@decorators.build_command
@decorators.handle_all_errors()
@click.pass_context
def push(context, jobs_names, base_dir, force, allow_overwrite,
         context_overrides, trigger_builds, block_builds, build_parameters,
         confirm_replace):
    """
    Push JOBS to the Jenkins server.

    If no JOBS are specified, push all jobs.
    """
    session = jenkins_api.auth(base_dir)
    _check_push_flag(context, base_dir, force)
    jobs_defs = repository.get_jobs_defs(base_dir)
    pipelines = repository.get_pipelines(base_dir)
    _check_for_gui_modifications(context, session, base_dir, jobs_names,
                                 allow_overwrite, context_overrides)
    remaining_jobs = list(jobs_names)
    while remaining_jobs:
        with click.progressbar(remaining_jobs, label='Pushing jobs') as bar:
            mismatch_info, remaining_jobs = _push_jobs(session, remaining_jobs,
                                                       bar, base_dir,
                                                       pipelines, jobs_defs,
                                                       context_overrides)
        if mismatch_info:
            job_name, expected_type, pushed_type = mismatch_info
            if _confirm_mismatching_job_type_overwrite(job_name,
                                                       expected_type,
                                                       pushed_type,
                                                       confirm_replace):
                jenkins_api.delete_job(
                    session,
                    job_name
                )
            else:
                break
    pushed_jobs = sorted(set(jobs_names).difference(remaining_jobs))
    utils.print_jobs_list('Jobs not pushed:', remaining_jobs, fg='yellow')
    utils.print_jobs_list('Pushed jobs:', pushed_jobs, fg='green')
    if trigger_builds:
        build.do_build(session, jobs_names, base_dir, block_builds,
                       build_parameters)


def _check_for_gui_modifications(context, session, base_dir, jobs_names,
                                 allow_overwrite, context_overrides):
    if allow_overwrite:
        return
    gui_was_modified = False
    for job_name in jobs_names:
        try:
            conf = jenkins_api.get_job_config(session, job_name)
        except exceptions.JobNotFound:
            continue
        saved_hash, conf = jobs.extract_hash_from_description(conf)
        actual_hash = jobs.get_conf_hash(conf)
        if saved_hash is not None and saved_hash != actual_hash:
            utils.sechowrap('It looks like job "%s" has been modified in the '
                            'Jenkins GUI:' % job_name, fg='red', bold=True)
            utils.sechowrap('')
            diff.print_job_diff(session, base_dir, job_name, context_overrides,
                                reverse=True)
            utils.sechowrap('')
            gui_was_modified = True
    if gui_was_modified:
        utils.sechowrap('')
        utils.sechowrap('You can force push the jobs with the '
                        '--allow-overwrite flag', fg='red')
        context.exit(1)


def _push_jobs(session, jobs_names, progress_bar, base_dir, pipelines,
               jobs_defs, context_overrides):
    templates_dir = repository.get_templates_dir(base_dir)
    remaining_jobs = list(jobs_names)
    mismatch_info = None
    for job_name in progress_bar:
        job_def = jobs_defs[job_name]
        pipe_info = pipelines.get(job_name)
        final_conf, _ = jobs.render_job(templates_dir, job_def['template'],
                                        job_def['context'], pipe_info,
                                        insert_hash=True,
                                        context_overrides=context_overrides)
        if conf.get(base_dir, ['server', 'disable_jobs_from_gui']):
            server_conf = jenkins_api.get_job_config(session, job_name)
            final_conf = jobs.transfuse_disabled_flag(server_conf, final_conf)
        try:
            jenkins_api.push_job_config(
                session,
                job_name,
                final_conf
            )
        except exceptions.JobTypeMismatch as exc:
            mismatch_info = (job_name, exc.expected_type, exc.pushed_type)
            break
        remaining_jobs.pop(0)
    return mismatch_info, remaining_jobs


def _confirm_mismatching_job_type_overwrite(job_name, expected_type,
                                            pushed_type, confirm_replace):
    utils.sechowrap('')
    utils.sechowrap('Failed to push %s.' % job_name, fg='red', bold=True)
    utils.sechowrap('')
    utils.sechowrap('The job type on the server does not match the job type '
                    'being pushed:', fg='red')
    utils.sechowrap('  expected: %s' % expected_type, fg='red')
    utils.sechowrap('  pushed: %s' % pushed_type, fg='red')
    utils.sechowrap('')
    if confirm_replace:
        return click.confirm(click.style(click.wrap_text(
            'Do you want to delete the old job and replace it with this one? '
            'you will loose all the builds history'
        ), fg='yellow'))
    else:
        return True


def _check_push_flag(context, base_dir, force):
    if force or not conf.get(base_dir, ['server', 'forbid_push']):
        return
    utils.sechowrap('Pushes are not allowed for this repository', fg='red',
                    bold=True)
    utils.sechowrap('')
    utils.sechowrap('The push command is explicitely disabled for this '
                    'repository. This usually means that pushes are done '
                    'server-side with a SCM hook.', fg='red')
    utils.sechowrap('')
    utils.sechowrap('If you really know what you\'re doing, you can use the '
                    '--force flag to push anyway.', fg='red')
    context.exit(1)
