
import json, re

from sqlite3 import IntegrityError

from falias.util import uni

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

class Login(object):
    def __init__(self, id = None):
        self.id = id
        self.email = ''
        self.rights = []
        super(Login, self).__init__()
    #enddef

    def get(self, req):
        tran = req.db.transaction(req.logger)
        c = tran.cursor()
        c.execute("SELECT email, rights, enabled "
                    "FROM login WHERE login_id = %s", self.id)
        row = c.fetchone()
        if not row: return False
        self.email, rights, self.enabled = row
        self.rights = json.loads(rights)
        tran.commit()
        return True
    #enddef

    def add(self, req):
        if not self.check_email(): return BAD_EMAIL
        if not self.check_passwd(): return WEAK_PASSWD
        if self.passwd != self.again: return PASSWD_NOT_SAME

        tran = req.db.transaction(req.logger)
        c = tran.cursor()

        try:        # email must be uniq
            c.execute("INSERT INTO login (email, rights, passwd) "
                    "VALUES ( %s, %s, %s )",
                    (self.email, json.dumps(self.rights), self.passwd))
            self.id = c.lastrowid
        except IntegrityError as e:
            return LOGIN_EXIST
        tran.commit()
    #enddef

    def _mod(self, req, keys, vals):
        keys = list( '%s = %%s' % k for k in keys )
        vals.append(self.id)

        tran = req.db.transaction(req.logger)
        c = tran.cursor()

        try:        # email must be uniq
            c.execute("UPDATE login SET %s WHERE login_id = %%s " % \
                        ', '.join(keys), vals)
        except IntegrityError as e:
            return LOGIN_EXIST

        if not c.rowcount:
            return LOGIN_NOT_EXIST
        
        tran.commit()
    #enddef


    def mod(self, req):
        keys = ['email', 'rights']
        vals = [self.email, json.dumps(self.rights)] 
        
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
        keys = ['email']
        vals = [self.email] 
        
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
        tran = req.db.transaction(req.logger)
        c = tran.cursor()

        c.execute("UPDATE login SET enabled = %s WHERE login_id = %s",
                        (self.enabled, self.id))
        
        if not c.rowcount:
            return LOGIN_NOT_EXIST

        tran.commit()
    #enddef

    def bind(self, form, salt):
        self.id = form.getfirst('login_id', fce = int) if 'login_id' in form else None
        self.email = form.getfirst('email', '', uni)
        self.plain = form.getfirst('passwd', '', uni)
        self.passwd = sha1_sdigest(form.getfirst('passwd', '', uni), salt)
        self.again = sha1_sdigest(form.getfirst('again', '', uni), salt)
        self.rights = form.getlist('rights', uni)
    #enddef

    def simple(self):
        rv = Login(self.id)
        rv.email = self.email
        rv.rights = self.rights
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
        tran = req.db.transaction(req.logger)
        c = tran.cursor()
        c.execute("SELECT login_id, rights FROM login "
                "WHERE email = %s AND passwd = %s AND enabled = 1",
                (self.email, self.passwd))
        row = c.fetchone()
        tran.commit()

        if not row: return False
        self.id = row[0]
        self.rights = json.loads(row[1])
        return True
    #enddef

    def check(self, req):
        try:
            self.get(req)
        except:
            return False
        return bool(self.enabled)
    #enddef

    @staticmethod
    def list(req, pager):
        tran = req.db.transaction(req.logger)
        c = tran.cursor()
        c.execute("SELECT login_id, email, rights, enabled "
                    "FROM login ORDER BY email LIMIT %s, %s",
                    (pager.offset, pager.limit))
        items = []
        row = c.fetchone()
        while row is not None:
            login = Login(row[0])
            login.email = row[1]
            login.rights = json.loads(row[2])
            login.enabled = row[3]
            items.append(login)
            row = c.fetchone()
        #endwhile

        c.execute("SELECT count(*) FROM login")
        pager.total = c.fetchone()[0]
        tran.commit()

        return items
    #enddef

#endclass
