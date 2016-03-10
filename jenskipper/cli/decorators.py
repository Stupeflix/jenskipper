import functools
import sys

import click

from .. import repository
from .. import conf
from .. import exceptions
from .. import utils


def repos_command(func):
    '''
    Base options for repository commands.
    '''

    @click.option('--jk-dir', '-d', default='.', help='Location of the '
                  'jenskipper repository (default: the current directory).')
    @functools.wraps(func)
    def wrapper(jk_dir, **kwargs):
        base_dir = repository.check_dir_is_in_repository(jk_dir)
        return func(base_dir=base_dir, **kwargs)

    return wrapper


def jobs_command(func):
    '''
    Base options for jobs that take a list of jobs names.

    Expects a *base_dir* argument.
    '''

    @click.argument('jobs_names', metavar='JOBS', nargs=-1)
    @functools.wraps(func)
    def wrapper(jobs_names, base_dir, **kwargs):
        jobs_defs = repository.get_jobs_defs(base_dir)
        if not jobs_names:
            jobs_names = jobs_defs.keys()
        unknown_jobs = set(jobs_names).difference(jobs_defs)
        if unknown_jobs:
            click.secho('Unknown jobs: %s' % ', '.join(unknown_jobs), fg='red',
                        bold=True)
            sys.exit(1)
        return func(jobs_names=jobs_names, base_dir=base_dir, **kwargs)

    return wrapper


def handle_conf_errors(func):
    '''
    Print nice error messages on configuration validation errors.
    '''
    # TODO: find more DRY way to handle these exceptions

    @functools.wraps(func)
    def wrapper(**kwargs):
        try:
            return func(**kwargs)
        except exceptions.ConfError as exc:
            conf.print_validation_errors(exc.conf,
                                         exc.validation_results)
            sys.exit(1)

    return wrapper


def context_command(func):
    '''
    Base options for jobs that can override context variables on the command
    line.

    The command receives a *context_overrides* argument, a dict ready to be
    deep merged in templates contexts.
    '''

    @click.option('--context', '-c', 'context_vars', multiple=True,
                  metavar='VAR=VALUE', help='Override context VAR with '
                  'VALUE; use --context multiple times to override multiple '
                  'variables.')
    @functools.wraps(func)
    def wrapper(context_vars, **kwargs):
        try:
            context_overrides = parse_context_vars(context_vars)
        except exceptions.MalformedContextVar as exc:
            click.secho('Malformed context var in command-line: %s' % exc,
                        fg='red', bold=True)
            sys.exit(1)
        return func(context_overrides=context_overrides, **kwargs)

    return wrapper


def parse_context_vars(context_vars):
    ret = {}
    for spec in context_vars:
        path, sep, value = spec.partition('=')
        if sep != '=':
            raise exceptions.MalformedContextVar(spec)
        path = path.split('.')
        utils.set_path_in_dict(ret, path, value, inplace=True)
    return ret
