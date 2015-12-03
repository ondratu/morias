
from falias.util import uni, nint

from time import time
from hashlib import sha256

import re

from core.login import sha1_sdigest

MIN_PASSWD_LEN = 6

# states    (errors from 1, warnings from 100, info from 200)
OK = 0
BAD_EMAIL = 1
WEAK_PASSWD = 2
PASSWD_NOT_SAME = 4
LOGIN_EXIST = 8
LOGIN_NOT_EXIST = 16
CONDITION_NOT_CONFIRMED = 32

PASSWD_WAS_SET = 64
REQUEST_FOR_EMAIL = 128
BAD_SERVIS_HASH = 256

re_email = re.compile(r"^[\w\.]+@[\w\.]{3,}$")
re_upcase = re.compile(r"[A-Z]+")
re_number = re.compile(r"[0-9]+")

_drivers = ("sqlite",)


def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "login_" + req.db.driver
    return __import__("lib." + m).__getattribute__(m)


class Login(object):
    def __init__(self, id=None):
        self.id = id
        super(Login, self).__init__()

    def get(self, req):
        m = driver(req)
        return m.get(self, req)

    def add(self, req, sign_up=False):
        error = 0
        if not self.check_email():
            error |= BAD_EMAIL
        if not self.check_passwd():
            error |= WEAK_PASSWD
        if self.passwd != self.again:
            error |= PASSWD_NOT_SAME
        if sign_up and 'conditions' not in self.data:
            error |= CONDITION_NOT_CONFIRMED
        if error:
            return error

        self.history = [(int(time()),   # (timestamp, action)
                         'sign_up' if sign_up else 'created')]
        source_string = '%s%s' % (self.data, self.email)
        self.service_hash = sha256(source_string).hexdigest()
        m = driver(req)
        return m.add(self, req)
    # enddef

    def _mod(self, req, keys, vals, condition=None):
        m = driver(req)
        return m._mod(self, req, keys, vals, condition)

    def mod(self, req):
        keys = ['email', 'rights', 'data']
        vals = [self.email, self.rights, self.data]

        error = 0
        if not self.check_email():
            error |= BAD_EMAIL
        if self.plain or self.passwd != self.again:     # if passwd was set
            if not self.check_passwd():
                error |= WEAK_PASSWD
            if self.passwd != self.again:
                error |= PASSWD_NOT_SAME

            keys.append('passwd')
            vals.append(self.passwd)

        if error:
            return error

        m = driver(req)
        c = m._transaction(req)
        retval = m._mod(self, c, keys, vals)
        m._commit(c)

        if retval:      # OK = 0 so no return
            return retval

        if self.plain:
            return PASSWD_WAS_SET
    # enddef

    def pref(self, req, email=None):
        keys = ['data']
        vals = [self.data]

        error = 0
        if email and not re_email.match(email):
            error |= BAD_EMAIL
        if self.plain or self.passwd != self.again:     # if passwd was set
            if not self.check_passwd():
                error |= WEAK_PASSWD
            if self.passwd != self.again:
                error |= PASSWD_NOT_SAME

            keys.append('passwd')
            vals.append(self.passwd)

        if error:
            return error

        if email:
            history = [(int(time()),   # (timestamp, action, parametr)
                       'change_email', email)]
            source_string = '%s%s' % (history, self.email)
            self.service_hash = sha256(source_string).hexdigest()
            keys.extend(['service_hash', 'history'])
            vals.extend([self.service_hash, history])

        m = driver(req)
        c = m._transaction(req)
        m._mod(self, c, keys, vals)
        m._commit(c)

        if self.plain:
            return PASSWD_WAS_SET
    # enddef

    def enable(self, req):
        m = driver(req)
        return m.enable(self, req)

    def log_in_link(self, req):
        history = [(int(time()),   # (timestamp, action)
                    'log_in_link')]
        source_string = '%s%s' % (history, self.email)
        self.service_hash = sha256(source_string).hexdigest()
        keys = ['service_hash', 'history']
        vals = [self.service_hash, history]

        m = driver(req)
        c = m._transaction(req)
        retval = m._mod(self, c, keys, vals, condition=('email', self.email))
        m._commit(c)
        return retval

    def bind(self, form, salt):
        self.id = form.getfirst('login_id', self.id, nint)
        self.email = form.getfirst('email', '', uni)
        self.plain = form.getfirst('passwd', '', uni)
        self.passwd = sha1_sdigest(form.getfirst('passwd', '', uni), salt)
        self.again = sha1_sdigest(form.getfirst('again', '', uni), salt)
        self.rights = form.getlist('rights', uni)
        # json data
        self.data = {}  # empty dictionary for now
        if 'conditions' in form:
            self.data['conditions'] = int(time())
    # enddef

    def simple(self):
        rv = Login(self.id)
        rv.md5 = self.md5       # using md5 checksum of login state
        return rv

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

    @staticmethod
    def check_verify(item, key, ttl=-1):
        if ttl > 0:
            return item[1] == key and (item[0] + ttl) >= time()
        else:
            return item[1] == key

    def find(self, req):
        m = driver(req)
        return m.find(self, req)

    def check(self, req):
        _md5 = self.md5
        if self.get(req):
            return _md5 == self.md5
        return False

    def verify(self, req, service_hash):
        """Verify servis hash.

        Return:
          * Login instance if service_hash is for log_in_link
          * Error code if service_hash is bad or expired or if any other fails
          * None if all works fine
        """
        condition = ('service_hash', service_hash)
        ttl = req.cfg.login_ttl_of_password_link * 60   # to seconds

        m = driver(req)
        c = m._transaction(req)
        if m._get(self, c, condition) is False:
            return BAD_SERVIS_HASH
        last = self.history[-1]

        if Login.check_verify(last, 'sign_up') \
                or Login.check_verify(last, 'created'):
            m._mod(self, c, ['enabled', 'service_hash'], [1, None], condition)
            m._commit(c)
            return OK
        elif Login.check_verify(last, 'log_in_link', ttl):
            if self.enabled:
                m._commit(c)
                return True
            else:
                m._mod(self, c, ['service_hash'], [None], condition)
                m._commit(c)
                return BAD_SERVIS_HASH
        elif Login.check_verify(last, 'change_email'):
            self.new_email = last[2]
            rv = m._mod(self, c, ['email', 'service_hash'],
                        [self.new_email, None], condition)
            if rv == OK:
                m._commit(c)
            return rv
        else:
            return BAD_SERVIS_HASH
    # enddef

    @staticmethod
    def list(req, pager):
        m = driver(req)
        return m.item_list(req, pager)
# endclass
