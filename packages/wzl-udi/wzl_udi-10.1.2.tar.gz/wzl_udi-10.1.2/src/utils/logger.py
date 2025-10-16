import datetime
import logging
import logging.config
import os

import sys


class Logger(object):
    def __init__(self, path, level=None):
        self._path = path
        self.root_logger = logging.getLogger(None)
        self.root_logger.setLevel(logging.DEBUG)

        if len(sys.argv[0].split("\\")) > 1:
            filename = sys.argv[0].split("\\")[-1]
        else:
            filename = sys.argv[0].split("/")[-1]

        self.file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self._path, "{}_{}.txt".format(filename, datetime.datetime.now().isoformat()).replace(':', '-')), maxBytes=20 * 1024 ** 2,
            backupCount=3)
        self.file_handler.doRollover()
        if level is None:
            self.file_handler.setLevel(logging.DEBUG)
        else:
            self.file_handler.setLevel(level)
        self.console_handler = logging.StreamHandler()
        if level is None:
            self.console_handler.setLevel(logging.INFO)
        else:
            self.console_handler.setLevel(level)
        self.root_formatter = logging.Formatter('### %(levelname)-8s %(asctime)s  %(name)-40s ###\n%(message)s\n')
        self.file_handler.setFormatter(self.root_formatter)
        self.console_handler.setFormatter(self.root_formatter)
        self.root_logger.addHandler(self.file_handler)
        self.root_logger.addHandler(self.console_handler)

    def get(self, name=None):
        return logging.getLogger(name)

    def set_logging_level(self, level, target=''):
        if target == 'FileHandler':
            self.file_handler.setLevel(level)
        elif target == 'StreamHandler':
            self.console_handler.setLevel(level)
        else:
            self.console_handler.setLevel(level)
            self.file_handler.setLevel(level)
