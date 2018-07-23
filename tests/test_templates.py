import sys

import jinja2
import six

from jenskipper import templates
from jenskipper import exceptions


def test_render(data_dir):
    rendered, _ = templates.render(six.text_type(data_dir), 'template.txt',
                                   {'name': 'John'})
    assert rendered == 'My name is John'


def test_render_with_overrides(data_dir):
    rendered, _ = templates.render(six.text_type(data_dir),
                                   'template.txt',
                                   {'name': 'John'},
                                   context_overrides={'name': 'Jane'})
    assert rendered == 'My name is Jane'


def test_extract_jinja_error_undefined_variable(data_dir):
    tpl_name = 'template.txt'
    tpl_path = data_dir.join(tpl_name)
    try:
        templates.render(six.text_type(data_dir), tpl_name, {})
    except jinja2.UndefinedError:
        stack, error = templates.extract_jinja_error(sys.exc_info())
    assert stack == [
        '  File "%s", line 1' % tpl_path,
        '    My name is {{ name }}',
    ]
    assert error == "Undefined variable: 'name' is undefined"


def test_extract_jinja_error_syntax_error(data_dir):
    tpl_name = 'template_with_syntax_error.txt'
    try:
        templates.render(six.text_type(data_dir), tpl_name, {})
    except jinja2.TemplateSyntaxError:
        stack, error = templates.extract_jinja_error(sys.exc_info())
    tpl_path = data_dir.join(tpl_name)
    assert stack == [
        '  File "%s", line 1' % tpl_path,
        '    {{ foo',
    ]
    assert error == "Syntax error: unexpected end of template, expected " \
        "'end of print statement'"


def test_extract_jinja_error_with_fnames_prefix(data_dir):
    tpl_name = 'template.txt'
    try:
        templates.render(six.text_type(data_dir), tpl_name, {})
    except jinja2.UndefinedError:
        stack, error = templates.extract_jinja_error(sys.exc_info(),
                                                     six.text_type(data_dir))
    assert stack == [
        '  File "template.txt", line 1',
        '    My name is {{ name }}',
    ]
    assert error == "Undefined variable: 'name' is undefined"


def test_track_includes(data_dir):
    rendered, loaded_files = templates.render(six.text_type(data_dir),
                                              'template_with_include.txt',
                                              {'name': 'Jane'})
    assert rendered == 'My name is Jane'
    assert loaded_files == {
        data_dir.join('template_with_include.txt'),
        data_dir.join('template.txt')
    }


def test_template_with_raise(data_dir):
    tpl_name = 'template_with_raise.txt'
    try:
        templates.render(six.text_type(data_dir), tpl_name, {})
    except exceptions.TemplateUserError:
        stack, error = templates.extract_jinja_error(sys.exc_info())
    tpl_path = data_dir.join(tpl_name)
    assert stack == [
        '  File "%s", line 3' % tpl_path,
        '    {% raise "baz" %}',
    ]
    assert error == 'User error: baz'
