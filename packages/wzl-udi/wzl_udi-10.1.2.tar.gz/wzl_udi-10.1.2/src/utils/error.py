class BasicException(Exception):

    def __init__(self, description, stack_trace=None, predecessor=None):
        self._description = description
        self._stack_trace = stack_trace
        self._predecessor = predecessor

    def __str__(self):
        if self._predecessor is None:
            return "{}: {}".format(type(self), self._description)
        else:
            return "{} ({}): {}".format(type(self), type(self._predecessor), self._description)

    @property
    def stack_trace(self):
        return self._stack_trace


class DeviceException(BasicException):

    def __init__(self, description, stack_trace=None, predecessor=None):
        BasicException.__init__(self, description, stack_trace, predecessor)


class UserException(BasicException):

    def __init__(self, description):
        BasicException.__init__(self, description)


class SerialisationException(DeviceException):

    def __init__(self, description):
        BasicException.__init__(self, description)


class PathResolutionException(BasicException):

    def __init__(self, description, stack_trace=None, predecessor=None):
        BasicException.__init__(self, description, stack_trace, predecessor)
