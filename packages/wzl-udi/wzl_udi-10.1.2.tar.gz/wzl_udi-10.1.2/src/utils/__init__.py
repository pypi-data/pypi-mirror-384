import os
import sys

from .logger import Logger

path = './logs'
for aid, arg in enumerate(sys.argv):
    if arg == '--logging-path':
        if aid == len(sys.argv) - 1:
            print('ERROR: No path argument given!')
        else:
            path = sys.argv[aid+1]
        break


if not os.path.isdir(path):
    os.makedirs(path)
root_logger = Logger(path)
