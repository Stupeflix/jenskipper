from jenskipper.cli import check


def test_check_good_template():
    assert check.check(['default_job'], standalone_mode=False) == 0


def test_check_missing_template():
    assert check.check(['missing_template'], standalone_mode=False) == 1


def test_check_template_errors():
    assert check.check(['syntax_error'], standalone_mode=False) == 2
    assert check.check(['undefined_var'], standalone_mode=False) == 2


def test_check_errors_combine():
    assert check.check(['syntax_error', 'missing_template'],
                       standalone_mode=False) == 3
