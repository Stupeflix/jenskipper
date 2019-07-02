import difflib
import logging

try:
    from lxml import etree  # NOQA
    HAVE_LXML = True
except ImportError:
    HAVE_LXML = False
import click

from . import decorators
from .. import utils
from .. import repository
from .. import jenkins_api
from .. import conf
from .. import jobs
from .. import exceptions


logger = logging.getLogger(__name__)


@click.command()
@click.option('-r/-f', '--reverse/--no-reverse', help='Show reverse diffs '
              '(default order is remote -> local).', default=False)
@click.option('--names-only', '-s', is_flag=True, help='Only show names '
              'of jobs that have a diff.')
@decorators.repos_command
@decorators.jobs_command(dirty_flag=True)
@decorators.context_command
@decorators.handle_all_errors()
@click.pass_context
def diff(context, jobs_names, base_dir, context_overrides, reverse,
         names_only):
    """
    Show diffs between JOBS in the local repository and on the server.

    If no JOBS are specified, diff all jobs.

    Return codes:

        0: the repository and the server are in sync

        1: a generic error occurred

        2: a job is present in the repository but not on the server

        3: repository and server are not in sync
    """
    if not HAVE_LXML:
        click.secho('This command works better if you install lxml:',
                    fg='yellow', bold=True)
        click.secho('  $ pip install lxml', fg='green')
    jenkins_url = conf.get(base_dir, ['server', 'location'])
    ret_code = 0
    for job_name in jobs_names:
        try:
            ret_code |= print_job_diff(base_dir, jenkins_url, job_name,
                                       context_overrides, reverse=reverse,
                                       names_only=names_only)
        except exceptions.JobNotFound:
            utils.sechowrap('')
            utils.sechowrap('Unknown job: %s' % job_name, fg='red', bold=True)
            utils.sechowrap('Job is present in the local repository, but not '
                            'on the Jenkins server.', fg='red')
            context.exit(2)
    ret_code = 3 if ret_code != 0 else 0
    context.exit(ret_code)


def print_job_diff(base_dir, jenkins_url, job_name, context_overrides=None,
                   reverse=False, names_only=False):
    """
    Print the diff between job *job_name* in the repository at *base_dir* and
    the server at *jenkins_url*.

    *context_overrides* must be a dict of values overriding the local job
    context.

    The diff shows what would change if the local job would be pushed to the
    server, unless *reverse* is true.

    Return the number of lines in the diff.
    """
    diff = get_job_diff(base_dir, jenkins_url, job_name,
                        context_overrides=context_overrides, reverse=reverse)
    if names_only:
        if diff:
            print job_name
    else:
        _print_diff(diff)
    return len(diff)


def get_job_diff(base_dir, jenkins_url, job_name, context_overrides=None,
                 reverse=False):
    """
    Get the diff lines printed by :func:`print_job_diff`.
    """
    logger.debug('diffing %s', job_name)
    if context_overrides is None:
        context_overrides = {}
    local_xml, _ = repository.get_job_conf(base_dir, job_name,
                                           context_overrides)
    with utils.add_lxml_syntax_error_context(local_xml, job_name):
        local_xml = _prepare_xml(local_xml)
    remote_xml, _ = jenkins_api.handle_auth(base_dir,
                                            jenkins_api.get_job_config,
                                            jenkins_url,
                                            job_name)
    with utils.add_lxml_syntax_error_context(remote_xml, job_name):
        remote_xml = _prepare_xml(remote_xml)
    from_text = remote_xml
    to_text = local_xml
    from_file = 'remote/%s.xml' % job_name
    to_file = 'local/%s.xml' % job_name
    if reverse:
        from_text, to_text = to_text, from_text
        from_file, to_file = to_file, from_file
    diff = difflib.unified_diff(from_text, to_text, fromfile=from_file,
                                tofile=to_file)
    return list(diff)


def _prepare_xml(xml):
    xml = utils.clean_xml(xml)
    xml = utils.unescape_xml(xml)
    xml = xml.replace('\r\n', '\n')
    _, xml = jobs.extract_hash_from_description(xml)
    return xml.splitlines(True)


def _print_diff(diff):
    for line in diff:
        line = line.rstrip()
        if line.startswith('---') or line.startswith('+++'):
            click.secho(line, fg='white', bold=True)
        elif line.startswith('-'):
            click.secho(line, fg='red')
        elif line.startswith('+'):
            click.secho(line, fg='green')
        else:
            click.secho(line)
