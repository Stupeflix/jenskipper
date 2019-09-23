import click
import coloredlogs

from .import_ import import_
from .show import show
from .push import push
from .list_jobs import list_jobs
from .fetch_new import fetch_new
from .diff import diff
from .build import build
from .prune import prune
from .test import test
from .sweep import sweep
from .log import log
from .patch import patch
from .dirty import print_dirty_jobs
from .get_artifact import get_artifact
from .status import get_job_status
from .auth import authenticate
from .delete import delete
from .check import check


@click.group()
@click.option('--log-level', '-l',
              type=click.Choice(('debug', 'info', 'warning', 'error')))
def main(log_level):
    """
    Pilot Jenkins from the command line.
    """
    coloredlogs.install(
        fmt='%(levelname)s %(message)s',
        level=log_level
    )


main.add_command(import_)
main.add_command(show)
main.add_command(push)
main.add_command(list_jobs)
main.add_command(fetch_new)
main.add_command(diff)
main.add_command(build)
main.add_command(prune)
main.add_command(test)
main.add_command(sweep)
main.add_command(log)
main.add_command(patch)
main.add_command(print_dirty_jobs)
main.add_command(get_artifact)
main.add_command(get_job_status)
main.add_command(authenticate)
main.add_command(delete)
main.add_command(check)
