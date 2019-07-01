import os
import os.path as op

import configobj
import validate
import click

from . import repository
from . import exceptions
from . import utils


THIS_DIR = op.dirname(__file__)


def get_user_conf_fname():
    return os.environ.get(
        'JK_USER_CONF',
        op.expanduser(op.join('~', '.config', 'jenskipper.conf'))
    )


def get_user_conf():
    """
    Get the global user configuration.

    Return a :class:`configobj.ConfigObj` object.
    """
    fname = get_user_conf_fname()
    dirname = op.dirname(fname)
    if not op.exists(dirname):
        os.makedirs(dirname)
    return configobj.ConfigObj(fname)


def get_repository_conf(base_dir):
    """
    Get the configuration for repository in *base_dir*.

    Return a :class:`configobj.ConfigObj` object.
    """
    fname = repository.get_conf_fname(base_dir)
    return configobj.ConfigObj(fname)


def get_conf(base_dir):
    """
    Get the actual configuration, built by merging the repository conf into the
    global user conf.
    """
    user_conf = get_user_conf()
    repos_conf = get_repository_conf(base_dir)
    configspec_fname = op.join(THIS_DIR, 'confspec.ini')
    merged_conf = configobj.ConfigObj(configspec=configspec_fname)
    merged_conf.merge(user_conf)
    merged_conf.merge(repos_conf)
    validator = validate.Validator()
    validation_results = merged_conf.validate(validator, preserve_errors=True)
    if validation_results is not True:
        raise exceptions.ConfError(merged_conf, validation_results)
    return merged_conf


def print_validation_errors(config, results):
    click.secho('Configuration validation failed:', fg='red', bold=True)
    for (section_list, key, _) in configobj.flatten_errors(config, results):
        if key is not None:
            click.secho('- the "%s" key in the section "%s" failed validation'
                        % (key, ', '.join(section_list)), fg='red')
        else:
            click.secho('- the following section was missing:%s ' %
                        ', '.join(section_list), fg='red')


def get(base_dir, path):
    """
    Get the value at *path* in the merged configurations (the configuration in
    base_dir + the user's configuration).
    """
    obj = get_conf(base_dir)
    keys = list(path)
    while keys:
        key = keys.pop(0)
        obj = obj[key]
    return obj


def set_in_user(path, value):
    """
    Write *value* in setting at *path*, in the global user configuration.
    """
    conf = get_user_conf()
    utils.set_path_in_dict(conf, path, value, inplace=True)
    conf.write()


def set_in_repos(base_dir, path, value):
    """
    Write *value* in setting at *path*, in the repository configuration in
    *base_dir*.
    """
    conf = get_repository_conf(base_dir)
    utils.set_path_in_dict(conf, path, value, inplace=True)
    conf.write()
