import os
import os.path as op

import pytest
import py.path


HERE = op.dirname(__file__)


@pytest.fixture
def data_dir(request):
    """
    Return a :class:`py.path.local` object pointing to the "data" directory
    relative to the test file.
    """
    return request.fspath.dirpath('data')


@pytest.fixture
def tmp_dir(request):
    """
    Return a :class:`py.path.local` object pointing to the "tmp" directory
    relative to the test file.
    """
    tmp_dir = request.fspath.dirpath('tmp')
    if tmp_dir.isdir():
        tmp_dir.remove()
    tmp_dir.mkdir()
    return tmp_dir


@pytest.fixture(scope='session', autouse=True)
def setup_global_cli_env_vars():
    param = op.join(HERE, 'cli', 'data')
    _setup_cli_env_vars(param)


@pytest.fixture
def setup_cli_env_vars(request):
    prev_vars = _setup_cli_env_vars(request.param)
    test_data = {k: py.path.local(os.environ[k])
                 for k in ('JK_DIR', 'JK_USER_CONF')}
    yield test_data
    os.environ.update(prev_vars)


def _setup_cli_env_vars(param):
    if isinstance(param, str):
        base_dir = param
        repos_name = 'repos'
    else:
        base_dir, repos_name = param
    prev_vars = {}
    for key, basename in [('JK_USER_CONF', 'jenskipper.conf'),
                          ('JK_DIR', repos_name)]:
        prev_vars[key] = os.environ.get(key)
        os.environ[key] = op.join(base_dir, basename)
    return prev_vars
