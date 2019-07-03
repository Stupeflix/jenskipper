import click
import requests
import sys

from . import decorators
from .. import jenkins_api
from .. import conf
from .. import utils


BUILD_SHORTCUTS = {
    'last': 'lastCompletedBuild',
    'last_failed': 'lastFailedBuild',
    'last_stable': 'lastStableBuild',
    'last_unstable': 'lastUnstableBuild',
}


@click.command('get-artifact')
@click.argument('job_name')
@click.argument('artifact')
@click.option('--build', '-b', help='Retrieve the artifact from this '
              'build number. These special values are also accepted: last, '
              'last_stable, last_failed, last_unstable (default: last).',
              default='last')
@click.option('--node-name', '-n', help='Retrieve the artifact from this '
              'node.')
@click.option('--output-file', '-o', type=click.File('wb'), default='-',
              help='Write artifact to this file (default: output it to '
              'stdout).')
@decorators.repos_command
@decorators.handle_all_errors()
@click.pass_context
def get_artifact(context, base_dir, job_name, artifact, build, node_name,
                 output_file):
    """
    Download an artifact.
    """
    jenkins_url = conf.get(base_dir, ['server', 'location'])
    real_build, jenkins_url = _resolve_build(context, base_dir, jenkins_url,
                                             job_name, build)
    print >> sys.stderr, 'Build number: %s' % real_build
    response, jenkins_url = jenkins_api.handle_auth(
        base_dir,
        jenkins_api.get_artifact,
        jenkins_url,
        job_name,
        real_build,
        artifact,
        node_name,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError:
        if response.status_code == 404:
            utils.sechowrap('Job, build or artifact not found', fg='red')
        else:
            utils.sechowrap('Unexpected HTTP error %s while trying to '
                            'retrieve artifact' % response.status_code,
                            fg='red')
        context.exit(1)
    _write_response(response, output_file)


def _write_response(response, output_file):
    for data in response.iter_content(4096):
        output_file.write(data)


def _resolve_build(context, base_dir, jenkins_url, job_name, build):
    if build not in BUILD_SHORTCUTS:
        try:
            return int(build), jenkins_url
        except ValueError:
            utils.sechowrap('Invalid build: %s' % build, fg='red')
            context.exit(1)
    try:
        job_data, jenkins_url = jenkins_api.handle_auth(base_dir,
                                                        jenkins_api.get_object,
                                                        jenkins_url,
                                                        '/job/%s' % job_name)
    except requests.HTTPError as exc:
        if exc.response.status_code == 404:
            utils.sechowrap('Unkown job: %s' % job_name)
        else:
            utils.sechowrap('Unexpected HTTP error %s while trying to '
                            'retrieve job data' % exc.response.status_code,
                            fg='red')
        context.exit(1)
    build_data = job_data[BUILD_SHORTCUTS[build]]
    if build_data is None:
        utils.sechowrap('No build data found for: %s' % build, fg='red')
        context.exit(1)
    real_build = build_data['number']
    return real_build, jenkins_url
