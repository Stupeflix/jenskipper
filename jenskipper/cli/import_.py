import os
import os.path as op
import click

from . import decorators
from .. import jenkins_api
from .. import jobs
from .. import pipelines
from .. import repository
from .. import conf
from .. import exceptions
from .. import utils


@click.command('import')
@click.argument('jenkins_url')
@click.argument('dest_dir')
@decorators.handle_all_errors(for_repos_command=False)
@click.pass_context
def import_(context, jenkins_url, dest_dir):
    """
    Import jobs from JENKINS_URL into DEST_DIR.
    """
    if op.exists(dest_dir):
        utils.sechowrap('Destination dir "%s" already exists' % dest_dir,
                        fg='red', bold=True)
        context.exit(1)
    jobs_names, jenkins_url = jenkins_api.handle_auth(dest_dir,
                                                      jenkins_api.list_jobs,
                                                      jenkins_url)
    with click.progressbar(jobs_names, label='Importing jobs') as bar:
        pipes_bits, jobs_templates = write_jobs_templates(dest_dir,
                                                          jenkins_url,
                                                          bar)
    write_jobs_defs(dest_dir, jobs_templates, 'w')
    write_pipelines(dest_dir, pipes_bits, 'w')
    _write_default_contexts(dest_dir)
    _write_conf(dest_dir, jenkins_url)
    utils.print_jobs_list('Imported jobs:', jobs_names, fg='green')


def write_jobs_templates(base_dir, jenkins_url, jobs_names,
                         allow_overwrite=False):
    """
    Retrieve job templates *jobs_names* from *jenkins_url* server in repository
    at *base_dir*.

    Return a ``(pipes_bits, jobs_templates)`` tuple, suitable for
    :func:`write_pipelines` and :func:`write_jobs_defs` respectively.

    If *allow_overwrite* is false, raise a
    :class:`jenskipper.exceptions.OverwriteError` if attempting to overwrite an
    existing file.
    """
    pipes_bits = {}
    jobs_templates = {}
    for job_name in jobs_names:
        config, jenkins_url = jenkins_api.handle_auth(
            base_dir,
            jenkins_api.get_job_config,
            jenkins_url,
            job_name
        )
        pipe_info, conf = jobs.extract_pipeline_conf(config)
        _, conf = jobs.extract_hash_from_description(config)
        if pipe_info is not None:
            pipes_bits[job_name] = pipe_info
        tpl_fname = _get_job_template_fname(base_dir, job_name)
        if not allow_overwrite and op.exists(tpl_fname):
            raise exceptions.OverwriteError(tpl_fname)
        tpl_dir = op.dirname(tpl_fname)
        if not op.exists(tpl_dir):
            os.makedirs(tpl_dir)
        with open(tpl_fname, 'w') as fp:
            fp.write(conf)
        jobs_templates[job_name] = tpl_fname
    return pipes_bits, jobs_templates


def write_jobs_defs(base_dir, jobs_templates, mode, pad_lines=0):
    """
    Write *jobs_templates* jobs definitions in the YAML file in repository at
    *base_dir*, opening the jobs definition file with *mode*.
    """
    fname = repository.get_jobs_defs_fname(base_dir)
    text = _format_default_jobs_defs(jobs_templates, base_dir)
    with open(fname, mode) as fp:
        fp.write('\n' * pad_lines)
        fp.write(text)


def write_pipelines(base_dir, pipes_bits, mode):
    """
    Write pipelines bits *pipes_bits* in the pipelines file of the repository
    in *base_dir*, opening the pipelines file with *mode*.
    """
    fname = repository.get_pipelines_fname(base_dir)
    text = pipelines.format_pipes_bits(pipes_bits)
    with open(fname, mode) as fp:
        fp.write(text)


def _write_default_contexts(base_dir):
    fname = repository.get_default_contexts_fname(base_dir)
    open(fname, 'w').close()


def _get_job_template_fname(base_dir, job_name):
    templates_dir = repository.get_templates_dir(base_dir)
    return op.join(templates_dir, '%s.xml' % job_name)


def _format_default_jobs_defs(jobs_templates, base_dir):
    # We don't use the yaml lib here to control formatting
    lines = []
    templates_dir = repository.get_templates_dir(base_dir)
    for job_name in sorted(jobs_templates):
        template_fname = jobs_templates[job_name]
        rel_template_fname = template_fname[len(templates_dir) + 1:]
        lines.append('%s:' % job_name)
        lines.append('  template: %s' % rel_template_fname)
        lines.append('')
    return '\n'.join(lines)


def _write_conf(base_dir, jenkins_url):
    canonical_url, _, _ = utils.split_auth_in_url(jenkins_url)
    conf.set_in_repos(base_dir, ['server', 'location'], canonical_url)
