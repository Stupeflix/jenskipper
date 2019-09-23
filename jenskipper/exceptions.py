import jinja2.exceptions


class JenskipperError(Exception):

    pass


class CyclicDependency(JenskipperError):

    def __init__(self, nodes):
        super(CyclicDependency, self).__init__(
            'involved nodes: %s' % ', '.join(str(n) for n in nodes)
        )
        self.nodes = nodes


class OverwriteError(JenskipperError):

    pass


class ConfError(JenskipperError):

    def __init__(self, conf, validation_results):
        self.conf = conf
        self.validation_results = validation_results
        super(ConfError, self).__init__('configuration validation failed')


class JobTypeMismatch(JenskipperError):
    """
    Raised in :func:`jenskipper.jenkins_api.push_job_conf` when the job type
    being pushed does not match the one defined in the GUI (for example, trying
    to push a freestyle job on a multi configuration one).
    """

    def __init__(self, expected_type, pushed_type):
        self.pushed_type = pushed_type
        self.expected_type = expected_type
        super(JobTypeMismatch, self).__init__('job type mismatch: expected '
                                              '"%s" but got "%s" instead' %
                                              (pushed_type, expected_type))


class JobNotFound(JenskipperError):

    pass


class BuildNotQueued(JenskipperError):

    pass


class MalformedContextVar(JenskipperError):

    pass


class MissingParametrizedBuildParameters(JenskipperError):

    pass


class MalformedBuildParameter(JenskipperError):

    pass


class BuildIsNotParametrized(JenskipperError):

    pass


class TemplateUserError(jinja2.exceptions.TemplateRuntimeError):
    """
    Raised by the {% raise 'error' %} extension.
    """

    pass
