from falias.util import nint, uni

_drivers = ("sqlite",)


def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "codebook_" + req.db.driver
    return __import__("lib." + m).__getattribute__(m)


class Item(object):
    ID = 'id'
    VALUE = 'value'
    TABLE = 'codebook'

    def __init__(self, id=None, value=''):
        self.id = id
        self.value = value

    def get(self, req):
        m = driver(req)
        row = m.get(self, req)
        if not row:
            return row
        self.id = row[self.ID]
        self.value = row[self.VALUE]

    def add(self, req, **kwargs):
        kwargs[self.VALUE] = self.value
        m = driver(req)
        return m.add(self, req, **kwargs)       # add to db

    def mod(self, req, **kwargs):
        kwargs[self.VALUE] = self.value
        m = driver(req)
        return m.mod(self, req, **kwargs)

    def delete(self, req):
        m = driver(req)
        return m.delete(self, req)

    def bind(self, form):
        self.id = form.getfirst('id', self.id, nint)
        self.value = form.getfirst('value', self.value, uni)

    @staticmethod
    def list(req, cls, pager, search=None):
        if pager.order not in ('id, value'):
            pager.order = 'value'

        m = driver(req)
        return m.item_list(req, cls, pager, search=search)
