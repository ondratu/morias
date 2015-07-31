# -*- coding: utf-8 -*-

from jinja2 import Environment, FileSystemLoader, DebugUndefined, \
        contextfunction
from falias.util import Object

from gettext import NullTranslations, translation
from datetime import datetime
from time import time
from json import dumps

from lang import get_lang, get_langs
from morias.lib.menu import correct_menu

class sdict(dict):
    def set(self, key, item):
        self.__setitem__(key, item)
        return ''

def to_unicode(obj):
    if isinstance(obj, str):
        obj = obj.decode('utf-8')
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = to_unicode(obj[k])
    elif isinstance(obj, list) or isinstance(obj, tuple) or isinstance(obj, set):
        obj = list(to_unicode(it) for it in obj )
    elif hasattr(obj, '__dict__'):
        for k in obj.__dict__.keys():
            obj.__dict__[k] = to_unicode(obj.__dict__[k])
    #else:
    #    print '>> ', obj, ' <<'

    return obj
#enddef

@contextfunction
def ctx(context):
    return context

@contextfunction
def check_right(ctx, right):
    if right in ctx['login'].rights or 'super' in ctx['login'].rights:
        return True
    return False
#enddef

@contextfunction
def match_right(ctx, rights):
    if not rights or 'super' in ctx['login'].rights:
        return True                 # not rights means means login have right

    if not set(ctx['login'].rights).intersection(rights):
        return False                # no rights match

    return True                     # some rights match
#enddef

def truncate(string, length = 255, killwords = True, end='...'):
    """ Only True yet """
    if len(string) > length:
        return string[:length] + end
    return string
#enddef

def fill(string, width = 80):
    return string + " "*(width-len(string))

def number(obj):
    return isinstance(obj, int) or isinstance(obj, float)

def jinja_template(filename, path, translations = NullTranslations, **kwargs):
    missing = []

    class MissingUndefined(DebugUndefined):

        def __recursion__(self, *args, **kwargs):
            missing.append(self._undefined_name)
            return MissingUndefined()

        __add__ = __radd__ = __mul__ = __rmul__ = __div__ = __rdiv__ = \
        __truediv__ = __rtruediv__ = __floordiv__ = __rfloordiv__ = \
        __mod__ = __rmod__ = __pos__ = __neg__ = __call__ = \
        __getitem__ = __lt__ = __le__ = __gt__ = __ge__ = __int__ = \
        __float__ = __complex__ = __pow__ = __rpow__ = \
        __recursion__

        def __getattribute__(self, name):
            if name[0] == '_':
                return DebugUndefined.__getattribute__(self, name)
            missing.append(self._undefined_name)
            return MissingUndefined(name = name)

        def __unicode__(self):
            if self._undefined_name is None:
                return ''
            missing.append(self._undefined_name)
            if kwargs['debug']:
                return '[Undefined] %s' % self._undefined_name
            return DebugUndefined.__unicode__(self)
    #endclass

    env = Environment(loader=FileSystemLoader(path),
                      undefined = MissingUndefined,
                      extensions=['jinja2.ext.i18n', 'jinja2.ext.do',
                                  'jinja2.ext.loopcontrols'])
    # debug functionality
    env.globals['_ctx_'] = ctx
    env.globals['_data_'] = kwargs.copy()
    env.globals['_miss_'] = missing
    env.globals['_template_'] = filename

    # jinja2 compatibility with old versions
    env.globals['length']   = len
    env.globals['truncate'] = truncate
    env.globals['number']   = number

    # some addons
    env.globals['ord'] = ord
    env.globals['now'] = time
    env.globals['datetime'] = datetime.fromtimestamp
    env.globals['jsonify'] = dumps
    env.globals['fill'] = fill

    env.filters['datetime'] = datetime.fromtimestamp
    env.filters['jsonify'] = dumps
    env.filters['fill'] = fill

    # morias functionality
    env.globals['check_right'] = check_right
    env.globals['match_right'] = match_right

    # gettext support
    env.install_gettext_translations(translations)

    template = env.get_template(filename)
    return template.render(kwargs)
#enddef

def morias_template(req, template, **kwargs):
    if 'lang' not in kwargs:                # lang could be set explicit
        kwargs['lang'] = get_lang(req)
        languages = get_langs(req)
    else:
        languages = (kwargs['lang'],)       # then use languages

    kwargs['debug'] = req.cfg.debug

    if hasattr(req, 'login'):
        kwargs['login'] = req.login

    kwargs['site'] = Object()
    kwargs['site'].name         = req.cfg.site_name
    kwargs['site'].description  = req.cfg.site_description
    kwargs['site'].keywords     = req.cfg.site_keywords
    kwargs['site'].author       = req.cfg.site_author
    kwargs['site'].copyright    = req.cfg.site_copyright
    kwargs['site'].styles       = req.cfg.site_styles
    kwargs['site'].this         = req.uri
    kwargs['site'].scheme       = req.scheme
    kwargs['site'].domain       = req.server_hostname

    kwargs['site'].modules      = req.cfg.modules
    kwargs['site'].footers      = req.cfg.footers

    kwargs['e'] = sdict()

    translations = translation('morias',
                                localedir = req.cfg.locales,
                                languages = languages,
                                fallback = True)

    return jinja_template(template, req.cfg.templates, translations, **kwargs)
#enddef

def generate_page(req, template, **kwargs):
    if 'content_type' in kwargs:
        req.content_type = kwargs['content_type']
        kwargs.pop('content_type')
    else:
        req.content_type = 'text/html'
    #endif

    if not 'menu' in kwargs:
        kwargs['menu'] = correct_menu(req, req.menu)
        correct_menu(req, req.static_menu, kwargs['menu'])

    return morias_template(req, template, **kwargs)
#enddef
