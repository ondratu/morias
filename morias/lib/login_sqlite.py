
from sqlite3 import IntegrityError
from hashlib import md5

import json

from lib.login import Login, LOGIN_EXIST, LOGIN_NOT_EXIST

def login_hash(email, passwd, enabled):
    """ return md5 checksum of email, password and enabled """
    return md5("%s%s%s" % (email, passwd, enabled)).hexdigest()

def get(self, req):
    tran = req.db.transaction(req.logger)
    tran.connection.create_function('hash', 3, login_hash)
    c = tran.cursor()
    c.execute("SELECT email, rights, enabled, data, hash(email, enabled, passwd) "
                "FROM logins WHERE login_id = %s", self.id)
    row = c.fetchone()
    if not row: return False
    self.email, rights, self.enabled, data, self.md5 = row
    self.rights = json.loads(rights)
    self.data = json.loads(data)
    tran.commit()
    return True
#enddef

def add(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    try:        # email must be uniq
        c.execute("INSERT INTO logins (email, rights, data, passwd) "
                "VALUES ( %s, %s, %s )",
                (self.email, json.dumps(self.rights), json.dumps(self.data),
                 self.passwd))
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
        c.execute("UPDATE logins SET %s WHERE login_id = %%s " % \
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

    c.execute("UPDATE logins SET enabled = %s WHERE login_id = %s",
                    (self.enabled, self.id))

    if not c.rowcount:
        return LOGIN_NOT_EXIST

    tran.commit()
#enddef

def find(self, req):
    tran = req.db.transaction(req.logger)
    tran.connection.create_function('hash', 3, login_hash)
    c = tran.cursor()
    c.execute("SELECT login_id, rights, data, hash(email, enabled, passwd) "
            " FROM logins WHERE email = %s AND passwd = %s AND enabled = 1",
            (self.email, self.passwd))
    row = c.fetchone()
    tran.commit()

    if not row: return False
    self.id = row[0]
    self.rights = json.loads(row[1])
    self.data = json.loads(row[2])
    self.md5 = row[3]
    return True
#enddef

def item_list(req, pager):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT login_id, email, rights, data, enabled "
                "FROM logins ORDER BY email LIMIT %s, %s",
                (pager.offset, pager.limit))
    items = []
    row = c.fetchone()
    while row is not None:
        login = Login(row[0])
        login.email = row[1]
        login.rights = json.loads(row[2])
        login.data = json.loads(row[3])
        login.enabled = row[4]
        items.append(login)
        row = c.fetchone()
    #endwhile

    c.execute("SELECT count(*) FROM logins")
    pager.total = c.fetchone()[0]
    tran.commit()

    return items
#enddef
