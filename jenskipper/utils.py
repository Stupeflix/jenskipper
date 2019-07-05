from xml.etree import ElementTree
import copy
import collections
import contextlib

import click


try:
    from lxml import etree
    HAVE_LXML = True
except ImportError:
    HAVE_LXML = False


def clean_xml(text):
    """
    Clean XML in *text*

    If :mod:`lxml` is available, remove blank text and pretty print it. If
    :mod:`lxml` is not available, return *text* as is.
    """
    text = text.strip()
    if HAVE_LXML:
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.fromstring(text, parser)
        return etree.tostring(tree, pretty_print=True, xml_declaration=True,
                              encoding='UTF-8')
    else:
        return text


def unescape_xml(xml):
    tree = ElementTree.fromstring(xml)
    return ElementTree.tostring(tree, encoding='UTF-8', method='xml')


def sechowrap(text, wrap_opts={}, **style):
    text = click.wrap_text(text, **wrap_opts)
    click.secho(text, **style)


def print_jobs_list(label, jobs_names, pad_lines=1, empty_label=None, **style):
    if jobs_names:
        click.secho('\n' * pad_lines, nl=False)
        click.secho('%s\n  %s' % (label, '\n  '.join(jobs_names)), **style)
    elif empty_label:
        click.secho(empty_label)


def _get_hostport(parsed_url):
    hostport = parsed_url.hostname
    if parsed_url.port is not None:
        hostport += ':%s' % parsed_url.port
    return hostport


def set_path_in_dict(dct, path, value, inplace=False):
    """
    Set value at *path* in *dct* to *value*.

    *path* is an iterable containing the path to the value. For example
    ``("foo", "bar")`` targets the sub dict "bar" at key "foo" of *dct*.

    By default *dct* is not modfied and a deep copy is returned, unless
    *inplace* is True
    """
    if inplace:
        cur = ret = dct
    else:
        cur = ret = copy.deepcopy(dct)
    keys = list(path)
    while keys:
        cur_key = keys.pop(0)
        if keys:
            cur = cur.setdefault(cur_key, {})
        else:
            cur[cur_key] = value
    return ret


def deep_merge(dct_a, dct_b, inplace=False):
    """
    Perform a "deep merge" of *dct_b* into *dct_a*.

    Return the merged result, in a new dict if *inplace* is false, or else in
    *dct_a*.
    """
    if inplace:
        ret = dct_a
    else:
        ret = copy.deepcopy(dct_a)
    flat_b = flatten_dict(dct_b)
    for path, value in flat_b.items():
        set_path_in_dict(ret, path, value, inplace=True)
    return ret


def flatten_dict(dct):
    """
    Flatten keys of (possibly nested) *dct*.

    >>> flatten_dict({'a': {'b': 'c'}})
    {('a', 'b'): 'c'}
    """
    items = _flatten_dict(dct, ())
    return dict(items)


@contextlib.contextmanager
def add_lxml_syntax_error_context(full_xml, context):
    """
    Augment :class:`lxml.etree.XMLSyntaxError` exceptions for
    :func:`format_lxml_syntax_error`.

    Usage::

        with add_lxml_syntax_error_context(full_xml, 'somefile.xml'):
            a_function_that_raises_XMLSyntaxError(full_xml)

    """
    if HAVE_LXML:
        try:
            yield
        except etree.XMLSyntaxError as exc:
            exc.full_xml = full_xml
            exc.context = context
            raise
    else:
        yield


def format_lxml_syntax_error(exc, context_lines=5, full_xml=False):
    """
    Format a :class:`lxml.etree.XMLSyntaxError`, showing the error's
    context_lines.

    *exc* should have been augmented with :func:`add_lxml_syntax_error_context`
    first.

    *name* is just a generic name indicating where the error occurred (for
    example the name of a job).

    *context_lines* is the number of lines to show around the error. If
    *full_xml* is true, show the entire XML.
    """
    lines = exc.full_xml.splitlines()
    err_line = exc.lineno - 1
    err_offset = exc.offset - 1
    if full_xml:
        start_line = 0
        end_line = None
    else:
        start_line = err_line - context_lines
        end_line = err_line + context_lines
    before_context = lines[start_line:err_line]
    error_line = lines[err_line]
    after_context = lines[err_line + 1:end_line]
    lines = [
        'XML syntax error in %s:' % click.style(exc.context, bold=True),
        '',
        click.style(exc.message, bold=True),
        '',
    ]

    # Get the error context lines
    xml_lines = []
    xml_lines += before_context
    xml_lines.append(
        click.style(error_line[:err_offset], fg='red') +
        click.style(error_line[err_offset], fg='red', bold=True) +
        click.style(error_line[err_offset + 1:], fg='red')
    )
    xml_lines_error_index = len(xml_lines)
    xml_lines += after_context

    # Add line numbers gutter
    gutter_width = len('%s' % (len(xml_lines) + start_line + 1))
    gutter_fmt = '%%%si' % gutter_width
    margin_width = 2
    xml_lines = [
        click.style(gutter_fmt % (i + start_line + 1),
                    fg='black', bold=True) +
        ' ' * margin_width + l
        for i, l in enumerate(xml_lines)
    ]

    # Add error marker
    xml_lines.insert(xml_lines_error_index,
                     ' ' * (err_offset + margin_width + gutter_width) + '^')

    lines += xml_lines
    return '\n'.join(lines)


def _flatten_dict(dct, ancestors=()):
    items = []
    for key, value in dct.items():
        path = ancestors + (key,)
        if isinstance(value, collections.Mapping):
            items.extend(_flatten_dict(value, path))
        else:
            items.append((path, value))
    return items
