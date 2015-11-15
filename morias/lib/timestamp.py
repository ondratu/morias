from poorwsgi import state

from os import makedirs, fstat
from os.path import dirname, exists
from sys import exc_info
from traceback import format_exception


def check_timestamp(req, filename):
    """ read timestamp file and returns it's modification time """
    if not exists(filename):
        # create file for next right read
        return write_timestamp(req, filename)

    with open(filename, 'rb') as f:
        return fstat(f.fileno()).st_mtime


def write_timestamp(req, filename):
    try:
        if not exists(dirname(filename)):
            makedirs(dirname(filename))
        with open(filename, 'wb') as f:
            return fstat(f.fileno()).st_mtime
    except:
        exc_type, exc_value, exc_traceback = exc_info()
        traceback = format_exception(exc_type,
                                     exc_value,
                                     exc_traceback)
        traceback = ''.join(traceback)
        req.log_error("Timestamp file %s could not be write:" %
                      filename, state.LOG_ERR)
        req.log_error(traceback, state.LOG_ERR)
        return 0
