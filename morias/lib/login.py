
import json, re

from falias.util import uni, nint

from core.login import sha1_sdigest

MIN_PASSWD_LEN  = 6

# states    (errors from 1, warnings from 100, info from 200)
BAD_EMAIL       = 1
WEAK_PASSWD     = 2
PASSWD_NOT_SAME = 3
LOGIN_EXIST     = 4
LOGIN_NOT_EXIST = 5

PASSWD_WAS_SET  = 200

re_email    = re.compile(r"^[\w\.]+@[\w\.]{3,}$")
re_upcase   = re.compile(r"[A-Z]+")
re_number   = re.compile(r"[0-9]+")

_drivers = ("sqlite",)

def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "login_" + req.db.driver
    return __import__("lib." + m).__getattribute__(m)
#enddef

class Login(object):
    def __init__(self, id = None):
        self.id = id
        super(Login, self).__init__()
    #enddef

    def get(self, req):
        m = driver(req)
        return m.get(self, req)

    def add(self, req):
        if not self.check_email(): return BAD_EMAIL
        if not self.check_passwd(): return WEAK_PASSWD
        if self.passwd != self.again: return PASSWD_NOT_SAME

        m = driver(req)
        return m.add(self, req)
    #enddef

    def _mod(self, req, keys, vals):
        m = driver(req)
        return m._mod(self, req, keys, vals)

    def mod(self, req):
        keys = ['email', 'rights', 'data']
        vals = [self.email, json.dumps(self.rights), json.dumps(self.data)]
        # FIXME!!!
        if self.plain or self.passwd != self.again:     # if passwd was set
            if not self.check_email(): return BAD_EMAIL
            if not self.check_passwd(): return WEAK_PASSWD
            if self.passwd != self.again: return PASSWD_NOT_SAME

            keys.append('passwd')
            vals.append(self.passwd)
        #endif

        self._mod(req, keys, vals)

        if self.plain:
            return PASSWD_WAS_SET
    #enddef

    def pref(self, req):
        keys = ['email', 'data']
        vals = [self.email, json.dumps(self.data)]

        if self.plain or self.passwd != self.again:     # if passwd was set
            if not self.check_email(): return BAD_EMAIL
            if not self.check_passwd(): return WEAK_PASSWD
            if self.passwd != self.again: return PASSWD_NOT_SAME

            keys.append('passwd')
            vals.append(self.passwd)
        #endif

        self._mod(req, keys, vals)

        if self.plain:
            return PASSWD_WAS_SET
    #enddef

    def enable(self, req):
        m = driver(req)
        return m.enable(self, req)

    def bind(self, form, salt):
        self.id = form.getfirst('login_id', self.id, nint)
        self.email = form.getfirst('email', '', uni)
        self.plain = form.getfirst('passwd', '', uni)
        self.passwd = sha1_sdigest(form.getfirst('passwd', '', uni), salt)
        self.again = sha1_sdigest(form.getfirst('again', '', uni), salt)
        self.rights = form.getlist('rights', uni)
        # json data
        self.data = ''  # TODO: json dump of dictionary

    #enddef

    def simple(self):
        rv = Login(self.id)
        rv.md5 = self.md5       # using md5 checksum of login state
        return rv
    #enddef

    def check_email(self):
        return True if re_email.match(self.email) else False

    def check_passwd(self):
        if len(self.plain) < MIN_PASSWD_LEN:
            return False
        if not re_upcase.search(self.plain):
            return False
        if not re_number.search(self.plain):
            return False
        return True
    #enddef

    def find(self, req):
        m = driver(req)
        print m, type(m)
        return m.find(self, req)

    def check(self, req):
        _md5 = self.md5
        if self.get(req):
            return _md5 == self.md5
        return False
    #enddef

    @staticmethod
    def list(req, pager):
        m = driver(req)
        return m.item_list(req, pager)

#endclass
