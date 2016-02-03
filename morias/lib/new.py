
from falias.util import uni, nint

# errors
EMPTY_TITLE = 1
EMPTY_BODY = 2

_drivers = ("sqlite",)


def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "new_" + req.db.driver
    return __import__("lib." + m).__getattribute__(m)


class New():
    def __init__(self, id=None):
        self.id = id

    def get(self, req):
        m = driver(req)
        return m.get(self, req)

    def add(self, req):
        if not self.title:
            return EMPTY_TITLE
        if not self.body:
            return EMPTY_BODY
        m = driver(req)
        m.add(self, req)
    # enddef

    def mod(self, req):
        if not self.title:
            return EMPTY_TITLE
        if not self.body:
            return EMPTY_BODY
        m = driver(req)
        return m.mod(self, req)
    # enddef

    def set_state(self, req, state):
        m = driver(req)
        return m.set_state(self, req, state)

    def bind(self, form, author_id=None):
        self.id = form.getfirst('new_id', self.id, nint)
        self.title = form.getfirst('title', '', uni)
        self.locale = form.getfirst('locale', '', uni)
        self.body = form.getfirst('body', '', uni)
        # if new is public, that is not draft
        self.public = form.getfirst('public', 0, int)
        self.state = 2 if self.public else form.getfirst('state', 1, int)
        self.data = {}
        if author_id:
            self.author_id = author_id
    # enddef

    @staticmethod
    def list(req, pager, body=False, **kwargs):
        if pager.order not in ('create_date', 'public_date', 'title',
                               'locale'):
            pager.order = 'create_date'

        m = driver(req)
        return m.item_list(req, pager, body, **kwargs)

    @staticmethod
    def test(req):
        m = driver(req)
        return m.test(req)
# endclass
