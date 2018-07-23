import click
import requests
import re
from six.moves import urllib
from six.moves.urllib import parse as urlparse

from . import conf
from . import exceptions


def auth(base_dir, jenkins_url=None):
    """
    Authenticate with the Jenkins server.

    Return a :class:`requests.Session` object with authentication baked in.
    """
    session = requests.session()

    # Retrieve user/password from conf
    if jenkins_url is None:
        jenkins_url = conf.get(base_dir, ['server', 'location'])
    session.jenkins_url = jenkins_url
    try:
        server_conf = conf.get(base_dir, [jenkins_url])
    except KeyError:
        pass
    else:
        session.auth = (server_conf['username'], server_conf['password'])

    # Get info page on Jenkins to check authentication
    info_url = urlparse.urljoin(jenkins_url, '/api/json')
    user_gave_auth = False
    while True:
        info_resp = session.get(info_url)
        try:
            info_resp.raise_for_status()
        except requests.HTTPError as exc:
            # Different versions of Jenkins return different HTTP status
            # codes...
            if exc.response.status_code in (401, 403, 500):
                username, password = _get_credentials(jenkins_url)
                session.auth = (username, password)
                user_gave_auth = True
            else:
                raise
        else:
            break

    # Propose to user to remember auth if he typed it
    if user_gave_auth:
        user_conf_fname = conf.get_user_conf_fname()
        if click.confirm('Save credentials in the global conf "%s"?' %
                         user_conf_fname):
            conf.set_in_user([jenkins_url, 'username'], username)
            conf.set_in_user([jenkins_url, 'password'], password)

    # Add crumbs headers to the session if the server demands it
    info_dict = info_resp.json()
    if info_dict['useCrumbs']:
        crumbs_url = urlparse.urljoin(jenkins_url, '/crumbIssuer/api/json')
        crumbs_resp = session.get(crumbs_url)
        crumbs_resp.raise_for_status()
        crumbs_dict = crumbs_resp.json()
        field = crumbs_dict['crumbRequestField']
        session.headers[field] = crumbs_dict['crumb']

    return session


def list_jobs(session):
    """
    Get the names of jobs on the server.
    """
    data = get_object(session, '')
    return [j['name'] for j in data['jobs']]


def _get_job_config_url(session, name):
    return urlparse.urljoin(session.jenkins_url, '/job/%s/config.xml' % name)


def get_job_config(session, name):
    """
    Get the XML configuration for job *name* from server.
    """
    url = _get_job_config_url(session, name)
    resp = session.get(url)
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        if exc.response.status_code == 404:
            raise exceptions.JobNotFound(name)
        raise
    return resp.text.encode('utf8')


def push_job_config(session, name, config, allow_create=True):
    """
    Replace the configuration of job *name* with *config* (a XML string) on the
    server.

    Raise a :class:`jenskipper.exceptions.JobTypeMismatch` error if the job
    type being pushed does not match the server-side job type (e.g. trying to
    push a multi-configuration job on a freestyle job).

    If *allow_create* is true, attempt to create the job if it does not exist
    on the server.
    """
    url = _get_job_config_url(session, name)
    resp = session.post(url, config)
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        if exc.response.status_code == 500:
            match = re.search(r'java.io.IOException: Expecting class '
                              r'([^\d\W][\w.]*) but got class ([^\d\W][\w.]*) '
                              r'instead', exc.response.text)
            if match is not None:
                expected_type, pushed_type = match.groups()
                raise exceptions.JobTypeMismatch(expected_type, pushed_type)
        elif exc.response.status_code == 404 and allow_create:
            return create_job(session, name, config)
        raise


def _get_credentials(jenkins_url):
    click.secho('Authentication error', fg='red', bold=True)
    click.secho('Please supply credentials to access %s' % jenkins_url)
    username = click.prompt('Username')
    password = click.prompt('Password', hide_input=True)
    click.secho('')
    return username, password


def delete_job(session, name):
    """
    Delete job named *name* on server.
    """
    url = urlparse.urljoin(session.jenkins_url, '/job/%s/doDelete' % name)
    resp = session.post(url)
    resp.raise_for_status()


def rename_job(session, name, new_name):
    """
    Rename job *name* to *new_name* on server.
    """
    url = urlparse.urljoin(session.jenkins_url, '/job/%s/doRename?newName=%s' %
                           (name, new_name))
    resp = session.post(url)
    resp.raise_for_status()


def create_job(session, name, conf):
    """
    Create a new job named *name* with *conf* on server.
    """
    url = urlparse.urljoin(session.jenkins_url, '/createItem?name=%s' %
                           urllib.quote_plus(name))
    resp = session.post(url, conf, headers={'Content-Type': 'application/xml'})
    resp.raise_for_status()


def build_job(session, job_name, parameters=None):
    """
    Trigger a build for *job_name*.

    To trigger a parametrized build, pass a dict containing the build
    parameters in *parameters*.

    Return the URL of the item in the builds queue.
    """
    if parameters:
        url = urlparse.urljoin(session.jenkins_url,
                               '/job/%s/buildWithParameters' % job_name)
    else:
        url = urlparse.urljoin(session.jenkins_url, '/job/%s/build' % job_name)
    resp = session.post(url, parameters)
    if resp.status_code == 400:
        raise exceptions.MissingParametrizedBuildParameters(job_name)
    if resp.status_code == 500:
        raise exceptions.BuildIsNotParametrized(job_name)
    resp.raise_for_status()
    if resp.status_code != 201:
        raise exceptions.BuildNotQueued(job_name)
    return resp.headers['location']


def get_build_log(session, build_url):
    """
    Retrieve the log for build at *build_url*.

    *build_url* is expected to be a full URL, as returned by
    :func:`jenskipper.cli.build.wait_for_builds`.
    """
    url = urlparse.urljoin(build_url, 'consoleText')
    resp = session.get(url)
    resp.raise_for_status()
    return resp.text


def get_object(session, path_or_url):
    """
    Get data from the ``api/json`` page of *path_or_url*.

    *path_or_url* can be a path relative to *session.jenkins_url* or a full
    jenkins URL.
    """
    parsed = urlparse.urlparse(path_or_url)
    url = urlparse.urljoin(session.jenkins_url, '%s/api/json' % parsed.path)
    resp = session.get(url)
    resp.raise_for_status()
    return resp.json()


def toggle_job(session, job_name, enable):
    """
    Enable or disable a job.
    """
    url = urlparse.urljoin(session.jenkins_url,
                           '/job/%s/%s' %
                           (job_name, 'enable' if enable else 'disable'))
    resp = session.post(url)
    resp.raise_for_status()


def get_artifact(session, job_name, build, artifact_name, node_name):
    """
    Get a build artifact.

    Return a :class:`requests.Response` object.
    """
    path = '/job/%s/%s' % (job_name, build)
    if node_name is not None:
        path += '/nodes=%s' % node_name
    path += '/artifact/%s' % artifact_name
    url = urlparse.urljoin(session.jenkins_url, path)
    return session.get(url, stream=True)
