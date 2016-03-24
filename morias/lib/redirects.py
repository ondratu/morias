from falias.util import uni, nint, Object

from morias.core.errors import ErrorValue

from morias.lib.timestamp import write_timestamp

_drivers = ("sqlite",)


class EmptySrc(ErrorValue):
    code = 1
    reason = 'empty_src'
    message = 'Empty source'


class EmptyDst(ErrorValue):
    code = 2
    reason = 'empty_dst'
    message = 'Empty destination'


class BadCode(ErrorValue):
    code = 3
    reason = 'bad_code'
    message = 'Bad code'


class BadSrc(ErrorValue):
    code = 4
    reason = 'bad_src'
    message = 'Bad source'


def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "redirects_" + req.db.driver
    return __import__("morias.lib." + m).lib.__getattribute__(m)


class Redirect(Object):
    def __init__(self, id=None, **kwargs):
        self.id = id
        super(Redirect, self).__init__(**kwargs)

    def from_row(self, row):
        for key in row.keys():
            setattr(self, key, row[key])

    def get(self, req, key='id'):
        m = driver(req)
        return m.get(self, req, key)

    def __check(self):
        if not getattr(self, 'src', None):
            return EmptySrc(redirect=self)
        if not self.src.startswith('/'):
            return BadSrc(redirect=self)
        if not getattr(self, 'dst', None):
            return EmptyDst(redirect=self)
        if getattr(self, 'code', 0) not in (301, 302):
            return BadCode(redirect=self)

    def add(self, req):
        rv = self.__check()
        if rv:
            return rv
        m = driver(req)
        rv = m.add(self, req)
        write_timestamp(req, req.cfg.redirects_timestamp)
        return rv
    # enddef

    def mod(self, req):
        rv = self.__check()
        if rv:
            return rv
        m = driver(req)
        rv = m.mod(self, req)
        write_timestamp(req, req.cfg.redirects_timestamp)
        return rv
    # enddef

    def set_state(self, req, state):
        m = driver(req)
        rv = m.set_state(self, req, state)
        write_timestamp(req, req.cfg.redirects_timestamp)
        return rv

    def delete(self, req):
        m = driver(req)
        rv = m.delete(self, req)
        write_timestamp(req, req.cfg.redirects_timestamp)
        return rv

    def bind(self, form):
        self.id = form.getfirst('id', self.id, nint)
        for attr in ('src', 'dst'):
            setattr(self, attr, form.getfirst(attr, '', uni))
        for attr in ('code', 'state'):
            setattr(self, attr, form.getfirst(attr, 0, int))
    # enddef

    @staticmethod
    def list(req, pager, search=None, state=None):
        if pager.order not in ('id', 'src', 'dst'):
            pager.order = 'id'

        m = driver(req)
        return m.item_list(req, pager, search, state)

    @staticmethod
    def test(req):
        m = driver(req)
        return m.test(req)
# endclass
