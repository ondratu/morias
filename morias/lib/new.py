
from falias.util import uni, nint

#errors
EMPTY_TITLE     = 1
EMPTY_BODY      = 2
NEW_NOT_EXIST   = 3

_drivers = ("sqlite",)

def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "new_" + req.db.driver
    return __import__("lib." + m).__getattribute__(m)
#enddef

class New():
    def __init__(self, id = None):
        self.id = id

    def get(self, req):
        m = driver(req)
        return m.get(self, req)
        
    def add(self, req):
        if not self.title: return EMPTY_TITLE
        if not self.body: return EMPTY_BODY

        m = driver(req)
        m.add(self, req)
    #enddef

    def mod(self, req):
        if not self.title: return EMPTY_TITLE
        if not self.body: return EMPTY_BODY

        m = driver(req)
        return m.mod(self, req)
    #enddef

    def enable(self, req):
        m = driver(req)
        return m.enable(self, req)

    def bind(self, form):
        self.id = form.getfirst('new_id', self.id, nint)
        self.title = form.getfirst('title', '', uni)
        self.locale = form.getfirst('locale', '', uni)
        self.body = form.getfirst('body', '', uni)
    #enddef

    @staticmethod
    def list(req, pager, body = False, **kwargs):
        if pager.order not in ('create_date', 'title', 'locale'):
            pager.order = 'create_date'
        
        m = driver(req)
        return m.item_list(req, pager, body, **kwargs)
    #enddef
#endclass
