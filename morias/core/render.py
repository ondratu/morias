from jinja2 import Environment, FileSystemLoader, DebugUndefined, \
        contextfunction
from gettext import NullTranslations, translation

from lang import get_lang, get_langs

class Object(object):
    def __contains__(self, key):
        return self.__dict__.__contains__(key)

class sdict(dict):
    def set(self, key, item):
        self.__setitem__(key, item)
        return ''

@contextfunction
def ctx(context):
    return context

def _truncate(string, length = 255, killwords = True, end='...'):
    """ Only True yet """
    if len(string) > length:
        return string[:length] + end
    return string
#enddef

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
            missing.append(self._undefined_name)
            return DebugUndefined.__unicode__(self)
    #endclass

    env = Environment(loader=FileSystemLoader(path),
                      undefined = MissingUndefined,
                      extensions=['jinja2.ext.i18n'])
    env.globals['_ctx_'] = ctx
    env.globals['_data_'] = kwargs.copy()
    env.globals['_miss_'] = missing
    env.globals['_template_'] = filename

    # jinja2 compatibility with old versions
    env.globals['length']    = len
    env.globals['truncate']  = _truncate

    # gettext support
    env.install_gettext_translations(translations)
    
    template = env.get_template(filename)
    return template.render(kwargs)
#enddef

def generate_page(req, template, **kwargs):
    if 'content_type' in kwargs:
        req.content_type = kwargs['content_type']
        kwargs.pop('content_type')
    else:
        req.content_type = 'text/html'
    #endif

    kwargs['lang'] = get_lang(req)
    kwargs['debug'] = req.cfg.debug
    
    kwargs['site'] = Object()
    kwargs['site'].name          = req.cfg.site_name
    kwargs['site'].description   = req.cfg.site_description
    kwargs['site'].keywords      = req.cfg.site_keywords
    kwargs['site'].author        = req.cfg.site_author
    kwargs['site'].copyright     = req.cfg.site_copyright
    kwargs['site'].styles        = req.cfg.site_styles

    kwargs['e'] = sdict()

    translations = translation('morias',
                                localedir = req.cfg.locales,
                                languages = get_langs(req),
                                fallback = True)

    return jinja_template(template, req.cfg.templates, translations, **kwargs)
#enddef
