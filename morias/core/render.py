from jinja2 import Environment, FileSystemLoader, DebugUndefined, \
        contextfunction

class JData: pass

@contextfunction
def ctx(context):
    return context

def _truncate(string, length = 255, killwords = True, end='...'):
    """ Only True yet """
    if len(string) > length:
        return string[:length] + end
    return string
#enddef

def jinja_template(data, filename, path):
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
                      undefined = MissingUndefined)
    env.globals['_ctx_'] = ctx
    env.globals['_data_'] = data.copy()
    env.globals['_miss_'] = missing

    env.globals['truncate']  = _truncate
    
    template = env.get_template(filename)
    return template.render(data)
#enddef
