"""
    This module library provide options from data backend. Use this library
    only for soft options like prices, themes and so on. Don't be remember, that
    you must obtain to right reload modified options from backend in ritht time.
"""

from poorwsgi import state

from falias.parser import smart_get
from falias.util import uni, nuni, islistable
from operator import attrgetter
from os import makedirs, fstat
from os.path import dirname, exists
from sys import exc_info
from traceback import format_exception

#errors
EMPTY_SECTION   = 0
EMPTY_OPTION    = 1
EMPTY_VALUE     = 2
UNKNOW_OPTION   = 3
BAD_VALUE       = 4

option_errors   = { EMPTY_SECTION   : 'empty_section',
                    EMPTY_OPTION    : 'empty_option',
                    EMPTY_VALUE     : 'empty_value',
                    UNKNOW_OPTION   : 'unknow_option',
                    BAD_VALUE       : 'bad_value' }

_drivers = ("sqlite",)

def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "options_" + req.db.driver
    return __import__("lib." + m).__getattribute__(m)
#enddef

class Option:
    def __init__(self, section = '', option = ''):
        self.section = section
        self.option = option
        self.value = None
    #enddef

    def get(self, req):
        m = driver(req)
        return m.get(self, req)


    def add(self, req):
        if not self.section: return EMPTY_SECTION
        if not self.option: return EMPTY_OPTION
        if not self.value: return EMPTY_VALUE
        m = driver(req)
        m.add(self, req)
        write_timestamp(req)
    #enddef

    def mod(self, req):
        if not self.section: return EMPTY_SECTION
        if not self.option: return EMPTY_OPTION
        if not self.value: return EMPTY_VALUE
        m = driver(req)
        rv = m.mod(self, req)
        write_timestamp(req)
        return rv
    #enddef

    def set(self, req):
        if not self.section: return EMPTY_SECTION
        if not self.option: return EMPTY_OPTION
        if not self.value: return EMPTY_VALUE
        cfgs = req.cfg.options.get(self.section, {}).get(self.option, {}).values()
        if not cfgs:
            return UNKNOWN_OPTION
        cls = cfgs[0][1]
        try:
            smart_get(self.value, cls)
        except:
            return BAD_VALUE

        m = driver(req)
        rv = m.option_set(self, req)
        write_timestamp(req)
        return rv
    #enddef

    def delete(self, req):
        m = driver(req)
        rv = m.delete(self, req)
        write_timestamp(req)
        return rv

    @staticmethod
    def list(req, pager, **kwargs):
        if pager.order not in ('section', 'option'):
            pager.order = 'section'

        onlydefault = kwargs.get('onlydefault', False)
        section = kwargs.get('section', None)
        module  = kwargs.get('module', None)

        items = []
        for sec, _sec in req.cfg.options.items():
            if section and sec != section:
                continue
            for opt, _opt in _sec.items():
                item = Option(sec, opt)
                item.modules = list()
                item.cls = None
                item.defaults = set()
                item.value = req.cfg.__dict__.get(
                                "%s_%s" % (sec,opt),    # fallback for core options
                                req.cfg.__dict__.get("%s" % (opt), None))
                if islistable(item.value):
                    item.value = ','.join((str(it) for it in item.value))

                for mod, _mod in _opt.items():
                    if module and mod != module:
                        continue
                    if onlydefault and _mod[0] is None:
                        continue
                    item.modules.append(mod)
                    item.defaults.add(_mod[0])
                    item.cls = _mod[1]

                if not item.modules:
                    continue

                items.append(item)
        #endfor

        if pager.order == 'option':
            items = sorted(items, key = attrgetter('section'))
            items = sorted(items, key = attrgetter('option'))
        else:
            items = sorted(items, key = attrgetter('option'))
            items = sorted(items, key = attrgetter('section'))

        pager.total = len(items)
        pager.limit = len(items) + 1
        return items
    #enddef

    @staticmethod
    def modules_list(req):
        items = set()
        for sec, _sec in req.cfg.options.items():
            for opt, _opt in _sec.items():
                items.update(_opt.keys())
        return items
    #enddef

    @staticmethod
    def sections_list(req):
        return req.cfg.options.keys()
    #enddef
#endclass

def load_options(req):
    for sec, _sec in req.cfg.options.items():
        for opt, _opt in _sec.items():
            if sec == 'morias' and opt == 'debug':  # too much danger
                continue
            if not _opt:                            # empty dictionary
                continue
            item = Option(sec, opt)
            cls = _opt.values()[0][1]
            var = "%s_%s" % (sec, opt)
            try:
                if item.get(req) is None:
                    continue
                req.cfg.__dict__[var] = smart_get(item.value, cls)
                req.log_error("Set cfg.%s from options DB to `%s'" % \
                                (var, item.value.encode('utf-8')), state.LOG_INFO)
            except:
                exc_type, exc_value, exc_traceback = exc_info()
                traceback = format_exception(exc_type,
                                             exc_value,
                                             exc_traceback)
                traceback = ''.join(traceback)
                req.log_error("Failed to load cfg.%s from options DB:" % var,
                                state.LOG_ERR)
                req.log_error(traceback, state.LOG_ERR)
#enddef

def check_timestamp(req):
    """ read timestamp file and returns it's modification time """
    if not exists (req.cfg.options_timestamp):
        return write_timestamp(req)         # create file for next right read

    with open(req.cfg.options_timestamp, 'rb') as f:
        return fstat(f.fileno()).st_mtime
#enddef

def write_timestamp(req):
    try:
        if not exists (dirname(req.cfg.options_timestamp)):
            makedirs(dirname(req.cfg.options_timestamp))
        with open(req.cfg.options_timestamp, 'wb') as f:
            return fstat(f.fileno()).st_mtime
    except:
        exc_type, exc_value, exc_traceback = exc_info()
        traceback = format_exception(exc_type,
                                     exc_value,
                                     exc_traceback)
        traceback = ''.join(traceback)
        req.log_error("Options timestamp file %s could not be write:" % \
                        req.cfg.options_timestamp, state.LOG_ERR)
        req.log_error(traceback, state.LOG_ERR)
        return 0
#enddef
