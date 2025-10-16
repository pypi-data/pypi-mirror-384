from ..utils.error import BasicException, DeviceException, UserException


class TypeException(DeviceException):

    def __init__(self, description):
        DeviceException.__init__(self, description)


class RangeException(DeviceException):

    def __init__(self, description):
        DeviceException.__init__(self, description)


class DimensionException(DeviceException):

    def __init__(self, description):
        DeviceException.__init__(self, description)


class InvalidModelException(UserException):

    def __init__(self, description):
        UserException.__init__(self, description)


class InvalidMappingException(UserException):

    def __init__(self, description):
        UserException.__init__(self, description)

class ChildNotFound(UserException):

    def __init__(self, description):
        UserException.__init__(self, description)


class ChildNotFoundException(DeviceException):

    def __init__(self, description):
        DeviceException.__init__(self, description)


class AmbiguousUUIDException(UserException):

    def __init__(self, description):
        UserException.__init__(self, description)


class ReadOnlyException(UserException):

    def __init__(self, uuid, name, description=None):
        if description is None:
            description = 'The parameter "{}" with UUID "{}" is a read-only parameter.'.format(name, uuid)
        UserException.__init__(self, description)


class NotImplementedException(UserException):
    def __init__(self, uuid, name, description=None):
        if description is None:
            description = 'The function "{}" with UUID "{}" is not implemented.'.format(name, uuid)
        UserException.__init__(self, description)


class InvokationException(DeviceException):
    def __init__(self, uuid, name, description=None):
        if description is None:
            description = 'Error when invoking "{}" with UUID "{}".'.format(name, uuid)
        DeviceException.__init__(self, description)
