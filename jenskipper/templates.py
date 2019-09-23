import traceback

import jinja2
import jinja2.nodes
import jinja2.ext
import click

from . import utils
from . import exceptions


class _RaiseExtension(jinja2.ext.Extension):
    """
    A :mod:`jinja2` extension to raise errors from templates::

        {% raise "this is an error" %}

    """

    tags = set(['raise'])

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        message_node = parser.parse_expression()
        return jinja2.nodes.CallBlock(
            self.call_method('_raise', [message_node], lineno=lineno),
            [], [], [], lineno=lineno
        )

    def _raise(self, msg, caller):
        raise exceptions.TemplateUserError(msg)


def render(templates_dir, template, context, context_overrides={}):
    """
    Render a job XML from job definition.

    If *insert_hash* is true, also include a hash of the configuration as text
    in the job description.

    :param templates_dir: location of the jobs templates
    :param template: the path to the job template, relative to *templates_dir*
    :param context: a dict containing the variables passed to the tamplate
    :param context_overrides:
        a mapping that will be deep merged in the final context
    :return:
        a ``(rendered_template, template_files)`` tuple, where
        ``template_files`` is the set of files that were loaded to render the
        template
    """
    loader = TrackingFileSystemLoader(templates_dir)
    env = jinja2.Environment(loader=loader,
                             autoescape=True,
                             undefined=jinja2.StrictUndefined,
                             extensions=[_RaiseExtension])
    template = env.get_template(template)
    context = utils.deep_merge(context, context_overrides)
    return template.render(**context), loader.loaded_files


def extract_jinja_error(exc_info, fnames_prefix=None):
    """
    Extract relevant informations from a Jinja2 exception.

    *exc_info* should be a ``(exc_type, exc_value, traceback)`` tuple, as
    returned by :func:`sys.exc_info`.

    Return a ``(stack, error)`` tuple, where *stack* a list of lines describing
    the stack that led to the error, and *error* the description of the error.

    Raise a :class:`TypeError` if the error is not a supported Jinja2 error.
    """
    exc_type, exc_value, tb = exc_info
    if exc_type is jinja2.UndefinedError:
        prefix = u'Undefined variable'
    elif exc_type is jinja2.TemplateSyntaxError:
        prefix = u'Syntax error'
    elif exc_type is exceptions.TemplateUserError:
        prefix = u'User error'
    else:
        raise TypeError(exc_type)

    stack_lines = []
    jinja_tb = [x for x in traceback.extract_tb(tb)
                if x[2] in ('top-level template code', 'template')]
    for file_name, line, func_name, text in jinja_tb:
        if fnames_prefix is not None:
            file_name = file_name[len(fnames_prefix) + 1:]
        stack_lines.append(u'  File "%s", line %s' % (file_name, line))
        stack_lines.append(u'    %s' % text)

    error_details = unicode(exc_value)
    error_details = error_details.rstrip('.')
    return stack_lines, u'%s: %s' % (prefix, error_details)


def print_jinja_error(stack_lines, error):
    click.secho('Traceback (most recent call last):')
    click.secho('')
    for line in stack_lines:
        click.secho(line)
    click.secho('')
    click.secho(error, fg='red', bold=True)


class TrackingFileSystemLoader(jinja2.FileSystemLoader):
    """
    A :class:`jinja2.FileSystemLoader` subclass that keeps track of the files
    it loads.

    :attr loaded_files: the set of loaded files
    """

    def __init__(self, *args, **kwargs):
        super(TrackingFileSystemLoader, self).__init__(*args, **kwargs)
        self.loaded_files = set()

    def get_source(self, *args, **kwargs):
        contents, filename, uptodate = \
            super(TrackingFileSystemLoader, self).get_source(*args, **kwargs)
        self.loaded_files.add(filename)
        return contents, filename, uptodate
