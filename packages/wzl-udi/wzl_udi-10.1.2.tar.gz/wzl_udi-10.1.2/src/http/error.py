from ..utils import root_logger
from ..utils.error import BasicException


logger = root_logger.get(__name__)


class ServerException(BasicException):

    def __init__(self, description, stack_trace=None, predecessor=None):
        BasicException.__init__(self, description, stack_trace, predecessor)


