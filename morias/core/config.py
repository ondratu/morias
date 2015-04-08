from poorwsgi import *
from falias.parser import Parser, Options
from time import strftime

from login import do_check_login

import os

config = None

class Config:
    def __init__(self, options, req):

        if 'morias_config' in options:
            inifile = options.get('morias_config')
            # TODO: check if file is readable
            req.log_error('Read config from file ...', state.LOG_INFO)
            p = Parser()
            p.read(inifile)
        else:
            req.log_error('Read config from options ...', state.LOG_INFO)
            p = Options(options)
        #endif

        #rpcAddress      = cfg.get('rpc', 'address', 'localhost')
        #rpcPort       = cfg.getint('rpc', 'port', 3030)

        self.debug      = p.get('morias', 'debug', False, cls = bool)

        self.templates  = p.get('morias', 'templates', cls = tuple,
                                                            delimiter = ':')
        self.modules    = p.get('morias', 'modules', cls = tuple)
        self.langs      = p.get('morias', 'langs', 'en,cs', cls = list)
        self.locales    = p.get('morias', 'locales', 'locales/')

        self.site_name          = p.get('site','name', "Morias")
        self.site_description   = p.get('site','description', "cms")
        self.site_keywords      = p.get('site','keywords', '', cls = tuple)
        self.site_author        = p.get('site','author', '')
        self.site_copyright     = p.get('site','copyright',
                                        strftime ("%%Y %s" % self.site_author.encode('utf-8')))
        self.site_styles        = p.get('site','styles', '', cls = tuple)

        for module in self.modules:
            req.log_error('Loading module %s' % module, state.LOG_INFO)
            self.load_module(p, req, module)

        """
        self.tmpPath    = cfg.get('main','tmp', '/tmp')
        self.origPath   = cfg.get('main','orig')
        self.pubPath    = cfg.get('main','pub')
        self.maintanancePath = cfg.get('maintanance','path')

        # memcache
        mc_servers = cfg.get('memcache', 'servers')
        mc_servers = map(lambda x: x.strip(), mc_servers.split(','))
        self.mc = Client(mc_servers, debug = cfg.getint('memcache', 'debug', 0))
        self.mcPrefix = cfg.get('memcache', 'prefix', '')
        self.mcExpiry = cfg.getint('memcache', 'expiry', 360) # 60 min

        # photo
        self.photosizes = cfg.get('photo','sizes')
        self.thumbsize = cfg.get('photo','thumbsize')
        self.previewwidth   = cfg.getint('photo','previewwidth')
        self.defaultsize = cfg.getint('photo','defaultsize')
        self.photoText = cfg.get('photo','text')
        self.histogramHeight = cfg.getint('photo','histheight')
        """
    #endef

    def load_module(self, p, req, module):
        #m = __import__("morias.%s" % module, globals())
        exec ("import %s as m" % module) in globals()

        if not '_check_conf' in m.__dict__:
            req.log_error('No config need for module %s...' % module, state.LOG_INFO)

        # check and set config values need for module
        else:
            for (sec, key, cls, dfl) in m._check_conf:
                var = "%s_%s" % (sec, key)
                if var in self.__dict__ and not isinstance(self.__dict__[var], cls):
                    raise TypeError("Option `%s` is not class instance `%s`",
                                    var, str(cls))
                if not var in self.__dict__:
                    self.__dict__[var] = p.get(sec, key, dfl, cls)
        #endif

        if '_call_conf' in m.__dict__:
            req.log_error('Config fn for module %s exist ...' % module, state.LOG_INFO)
            m._call_conf(self, p)
    #enddef

#endclass

@app.pre_process()
def load_config(req):
    global config

    if config is None:
        options = req.get_options()
        config = Config(options, req)

    req.cfg = config
    if 'morias_db' in config.__dict__:      # fast alias to db
        req.db = config.morias_db

    if 'morias_smtp' in config.__dict__:    # fast alias to smtp
        req.smtp = config.morias_smtp
        req.smtp.xmailer = 'Morias CMS (http://morias.zeropage.cz)'

    #req.templates = req.cfg.templates

    def logger(msg):
        req.log_error(msg, state.LOG_INFO)
    req.logger = logger

    do_check_login(req)                     # load login cookie avery time
#enddef
