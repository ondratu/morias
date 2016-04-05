
from poorwsgi import state

from sys import stderr, stdout, exc_info, exit
from traceback import format_exception
from os import waitpid, WNOHANG
import os

_drivers = ("sqlite",)
_pids = []


def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "jobs_" + req.db.driver
    return __import__("morias.lib." + m).lib.__getattribute__(m)


class Job():
    def __init__(self, path=None, pid=None, singleton=None):
        self.path = path
        self.pid = pid
        self.singleton = 1 if singleton else None

    def get(self, req):
        m = driver(req)
        return m.get(self, req)

    def add(self, req, progress=0, status=-1, message='Starting', **kwargs):
        kwargs.update({'progress': progress,
                       'status': status,
                       'message': message})
        self.data = kwargs
        m = driver(req)
        return m.add(self, req)

    def mod(self, req, **kwargs):
        self.data.update(kwargs)
        m = driver(req)
        return m.mod(self, req)

    def delete(self, req):
        m = driver(req)
        return m.delete(self, req)

    @staticmethod
    def list(req, pager, **kwargs):
        if pager.order not in ('timestamp', 'path'):
            pager.order = 'timestamp'

        m = driver(req)
        return m.item_list(req, pager, **kwargs)
# endclass


def clean_zombie(req):
    """ clean jobs(processes), which stop it's work """
    for pid in _pids:
        p, s = waitpid(pid, WNOHANG)
        if p:
            _pids.remove(p)   # or shuld be pid...
            req.log_error("Job with %d pid stop with status %d" % (p, s),
                          state.LOG_NOTICE)


def run_job(req, path, fn, singleton=None):
    pipe_out, pipe_in = os.pipe()
    pid = os.fork()
    if pid > 0:                     # parent process
        os.close(pipe_in)           # don't want write to pipe
        _pids.append(pid)
        req.log_error("Job crated with pid %d" % pid, state.LOG_NOTICE)
        with os.fdopen(pipe_out, 'r') as pipe:
            status = pipe.read(3)   # wait for job init
            return pid, (status == 'ACK')
    # end of parent process

    #     close all descriptor insead of out, err, and pipe_in
    out, err = (stdout.fileno(), stderr.fileno())
    for i in xrange(0, 500):
        if i == out or i == err or i == pipe_in:
            continue
        try:
            os.close(i)
        except OSError:
            pass
    # endfor

    #     reset log_error and logger function
    # TODO: copy level setting from poorwsgi
    def log_error(message, level):
        if level[0] < 5:
            stderr.write("[job: %d] <%s> %s\n" %
                         (os.getpid(), level[1], message))
        else:
            stdout.write("[job: %d] <%s> %s\n" %
                         (os.getpid(), level[1], message))

    def log_info(msg):
        log_error(msg, state.LOG_INFO)

    req.log_error = log_error
    req.log_info = log_info

    #     create job record and return status to master process
    job = Job(path=path, singleton=singleton)
    job.pid = os.getpid()
    job.login_id = req.login.id if req.login else 0
    with os.fdopen(pipe_in, 'w') as pipe:
        log_info('job add..')
        if job.add(req) is None:
            pipe.write('ERR')
            exit(1)             # process failed
        else:
            pipe.write('ACK')
    # endwith

    try:
        fn(req, job)
    except:
        exc_type, exc_value, exc_traceback = exc_info()
        traceback = format_exception(exc_type,
                                     exc_value,
                                     exc_traceback)
        traceback = ''.join(traceback)
        req.log_error(traceback, state.LOG_ERR)
        exit(1)
    finally:
        job.delete(req)
    exit(0)
# enddef
