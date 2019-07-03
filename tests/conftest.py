import os
import os.path as op

import pytest


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
    cli_data_dir = op.join(HERE, 'cli', 'data')
    _setup_cli_env_vars(cli_data_dir)


@pytest.fixture
def setup_cli_env_vars(request):
    prev_vars = _setup_cli_env_vars(request.param)
    yield
    os.environ.update(prev_vars)


def _setup_cli_env_vars(base_dir):
    prev_vars = {}
    for key, basename in [('JK_USER_CONF', 'jenskipper.conf'),
                          ('JK_DIR', 'repos')]:
        prev_vars[key] = os.environ.get(key)
        os.environ[key] = op.join(base_dir, basename)
    return prev_vars
