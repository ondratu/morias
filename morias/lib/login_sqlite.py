
import json

from sqlite3 import IntegrityError

from lib.login import Login, LOGIN_EXIST, LOGIN_NOT_EXIST

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

def enable(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    c.execute("UPDATE login SET enabled = %s WHERE login_id = %s",
                    (self.enabled, self.id))

    if not c.rowcount:
        return LOGIN_NOT_EXIST

    tran.commit()
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
