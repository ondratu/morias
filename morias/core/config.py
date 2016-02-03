from poorwsgi import app, state
from falias.parser import Parser, Options
from falias.util import Paths

from time import strftime
from gc import collect

from login import do_check_login


def option(*args):
    _len = len(args)
    if _len < 3:
        raise RuntimeError('Not enough option definition: %s' % args)
    sec, opt, cls = args[:3]
    dfl = args[3] if _len > 3 else None     # default value
    mod = args[4] if _len > 4 else False    # colud be set via option module
    doc = args[5] if _len > 5 else ''       # documentation for option module
    return sec, opt, cls, dfl, mod, doc


class Config:
    def load(self, options):
        if 'morias_config' in options:
            inifile = options.get('morias_config')
            # TODO: check if file is readable
            app.log_error('Read config from file ...', state.LOG_INFO)
            p = Parser()
            p.read(inifile)
        else:
            app.log_error('Read config from options ...', state.LOG_INFO)
            p = Options(options)
        # endif

        self.debug = p.get('morias', 'debug', False, cls=bool)

        self.templates = p.get('morias', 'templates', cls=Paths)
        self.footers = []    # modules could append path for it's footer
        self.modules = p.get('morias', 'modules', cls=tuple)
        self.langs = p.get('morias', 'langs', 'en,cs', cls=tuple)
        self.locales = p.get('morias', 'locales', 'locales/')

        self.site_name = p.get('site', 'name', "Morias")
        self.site_description = p.get('site', 'description', "cms")
        self.site_keywords = p.get('site', 'keywords', '', cls=tuple)
        self.site_author = p.get('site', 'author', '')
        self.site_copyright = p.get('site', 'copyright',
                                    strftime("%%Y %s" %
                                             self.site_author.encode('utf-8')))
        self.site_styles = p.get('site', 'styles', '', cls=tuple)

        self.options = {
            'morias': {
                'langs': {'morias.core':
                          ('en,cs', list, self.langs, True, '')},
            },
            'site': {
                'name':         {'morias.core':
                                 ('Morias', unicode, self.site_name,
                                  True, '')},
                'description':  {'morias.core':
                                 ('cms', unicode, self.site_description,
                                  True, '')},
                'keywords':     {'morias.core':
                                 ('', tuple, self.site_keywords, True, '')},
                'author':       {'morias.core':
                                 ('', unicode, self.site_author, True, '')},
                'copyright':    {'morias.core':
                                 ('', unicode, self.site_copyright, True, '')},
            }
        }

        for module in self.modules:
            app.log_error('Loading module %s' % module, state.LOG_INFO)
            self.load_module(p, module)

        """
        # memcache
        mc_servers = cfg.get('memcache', 'servers')
        mc_servers = map(lambda x: x.strip(), mc_servers.split(','))
        self.mc = Client(mc_servers, debug=cfg.getint('memcache', 'debug', 0))
        self.mcPrefix = cfg.get('memcache', 'prefix', '')
        self.mcExpiry = cfg.getint('memcache', 'expiry', 360) # 60 min
        """
    # endef

    def load_module(self, p, module):
        m = __import__("%s" % module, globals=globals(), fromlist=[None])
        # m = None
        # exec ("import %s as m" % module) in globals()

        if '_check_conf' not in m.__dict__:
            app.log_error('No config need for module %s...' % module,
                          state.LOG_INFO)

        # check and set config values need for module
        else:
            for it in m._check_conf:
                sec, opt, cls, dfl, mod, doc = option(*it)
                var = "%s_%s" % (sec, opt)
                if var in self.__dict__ \
                        and not isinstance(self.__dict__[var], cls):
                    raise TypeError("Option `%s` is not class instance `%s`",
                                    var, str(cls))
                if var not in self.__dict__:
                    self.__dict__[var] = p.get(sec, opt, dfl, cls)

                if not mod:     # option could not be set via option module
                    continue
                if sec not in self.options:
                    self.options[sec] = {}
                if opt not in self.options[sec]:
                    self.options[sec][opt] = {}
                self.options[sec][opt][module] = (dfl, cls, self.__dict__[var],
                                                  doc)
        # endif

        if '_call_conf' in m.__dict__:
            app.log_error('Config fn for module %s exist ...' % module,
                          state.LOG_INFO)
            m._call_conf(self, p)
    # enddef

    def log_error(self, message, level=state.LOG_INFO):
        """ application logger with default state.LOG_INFO log level """
        app.log_error(message, level)

    @property
    def cfg(self):
        """ baypass property for db operations at load modules """
        return self

    @property
    def db(self):
        """ baypass property for db operations at load modules """
        return self.morias_db

    @property
    def log_info(self):
        """ baypass property for db operations at load modules """
        return self.log_error
# endclass


@app.pre_process()
def config_to_request(req):
    if req.uri_rule in ('_debug_info_', '_send_file_', '_directory_index_'):
        return  # this methods no need this pre process

    req.cfg = config
    if 'morias_db' in config.__dict__:             # fast alias to db
        req.db = config.morias_db.copy()

    if 'morias_smtp' in config.__dict__:    # fast alias to smtp
        req.smtp = config.morias_smtp
        req.smtp.xmailer = 'Morias CMS (http://morias.zeropage.cz)'

    if 'no_check_login' in req.uri_handler.__dict__:
        return          # do not call do_check_login before some handlers

    do_check_login(req)                     # load login cookie avery time
# enddef


@app.post_process()
def call_gc(req):
    """It is better run gc directly in Python2.x."""
    collect()


# module config instance
config = Config()
