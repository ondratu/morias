from poorwsgi import *
from falias.unicode import uni
from ConfigParser import ConfigParser, NoSectionError, NoOptionError
from time import strftime


import gettext

config = None

def smart_get(value, cls = unicode, delimiter = ','):
    if issubclass(cls, unicode):
        return uni(value)
    if issubclass(cls, str):
        return value
    if issubclass(cls, bool):
        if value.lower() in ('true', 'yes', '1', 'on', 'enable'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off', 'disable'):
            return False
        else:
            raise ValueError("%s is not boolean value" % value)
    if issubclass(cls, list) or issubclass(cls, tuple):
        if value:
            return cls(map(lambda s: s.strip(), value.split(delimiter)))
        return cls()
    else:
        return cls(value)
#enddef


class SuperParser(ConfigParser):
    def get(self, section, option, default = None, cls = unicode, delimiter = ','):
        #cls = cls if default is None else default.__class__
        default = None if default is None else str(default)

        try:
            value = ConfigParser.get(self, section, option).strip()
        except NoSectionError:
            if default is None: raise
            value = default
        except NoOptionError:
            if default is None: raise
            value = default
        return smart_get(value, cls, delimiter)
#endclass

class SuperOptions:
    def __init__(self, options):
        self.o = options;

    def get(self, sec, key, default = None, cls = str, delimiter = ','):
        #cls = cls if default is None else default.__class__
        default = None if default is None else str(default)

        key = "%s_%s" % (sec, key)
        if default is None and key not in self.o:
            raise RuntimeError('Envirnonment variable `%s` is not set' % key)
        value = self.o.get(key, default).strip()
        return smart_get(value, cls, delimiter)
#endclass

class Config:
    def __init__(self, options, req):
    
        if 'morias_config' in options:
            inifile = options.get('morias_config')
            # TODO: check if file is readable
            req.log_error('Read config from file ...', state.LOG_INFO)
            p = SuperParser()
            p.read(inifile)
        else:
            req.log_error('Read config from options ...', state.LOG_INFO)
            p = SuperOptions(options)
        #endif        

        #dbg.logFile(cfg.get('main','debuglog'))
        #dbg.logMask(cfg.get('main','debugmask', 'I1E1F3'))
        #dbg.logBufSize(cfg.getint('main','debugsize', 1024))
            
        #rpcAddress      = cfg.get('rpc', 'address', 'localhost')
        #rpcPort       = cfg.getint('rpc', 'port', 3030)

        self.debug      = p.get('morias', 'debug', False, cls = bool)

        self.templates  = p.get('morias', 'templates')
        self.modules    = p.get('morias', 'modules', cls = tuple)
        self.langs      = p.get('morias', 'langs', 'en', cls = tuple)
        self.locales    = p.get('morias', 'locales', 'locales/')

        self.site_name          = p.get('site','name', "Morias")
        self.site_description   = p.get('site','description', "cms")
        self.site_keywords      = p.get('site','keywords', '', cls = tuple)
        self.site_author        = p.get('site','author', '')
        self.site_copyright     = p.get('site','copyright',
                                            strftime ("%%Y %s" % self.site_author))
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

        # smtp
        self.smtpserver = cfg.get('smtp','server','localhost')
        self.smtpsender = cfg.get('smtp','sender')
        self.smtpreply  = cfg.get('smtp','reply')
        self.smtpadmin  = cfg.get('smtp','admin')

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
        exec ("import morias.%s as m" % module) in globals()

        if not '_check_conf' in m.__dict__:
            req.log_error('No config need for module %s...' % module, state.LOG_INFO)
            return

        # check and set config values need for module
        for (sec, key, cls, dfl) in m._check_conf:
            var = "%s_%s" % (sec, key)
            if var in self.__dict__ and not isinstance(self.__dict__[var], cls):
                raise TypeError("Option `%s` is not class instance `%s`",
                                var, str(cls))
            if not var in self.__dict__:
                self.__dict__[var] = p.get(sec, key, dfl, cls)
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

    #req.templates = req.cfg.templates

    def logger(msg):
        req.log_error(msg, state.LOG_INFO)
    req.logger = logger
#enddef
