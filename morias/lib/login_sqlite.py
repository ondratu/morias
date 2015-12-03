
from sqlite3 import IntegrityError
from hashlib import md5

import json

from lib.login import Login, OK, LOGIN_EXIST, LOGIN_NOT_EXIST


def _transaction(req):  # static methos
    tran = req.db.transaction(req.logger)
    tran.connection.create_function('hash', 3, login_hash)
    c = tran.cursor()
    return c


def _commit(c):         # static method
    c.transaction.commit()


def _rollback(c):       # static method
    c.transaction.rollback()


def login_hash(email, passwd, enabled):
    """ return md5 checksum of email, password and enabled """
    return md5("%s%s%s" % (email, passwd, enabled)).hexdigest()


def _get(self, c, condition=None):
    if condition is None:
        condition = ('login_id', self.id)
    if condition[0] not in ('login_id', 'service_hash'):
        raise AssertionError('Unsuported condition %s' % condition)

    c.execute("""
        SELECT login_id, email, rights, enabled, data, history,
            hash(email, enabled, passwd)
        FROM logins WHERE %s = %%s
        """ % condition[0], condition[1])
    row = c.fetchone()
    if not row:
        return False
    self.id, self.email, rights, self.enabled, data, history, self.md5 = row
    self.rights = json.loads(rights)
    self.data = json.loads(data)
    self.history = json.loads(history)


def get(self, req):
    tran = req.db.transaction(req.logger)
    tran.connection.create_function('hash', 3, login_hash)
    c = tran.cursor()
    _get(self, c)
    tran.commit()
    return True
# enddef


def add(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    try:        # email must be uniq
        c.execute("""
            INSERT INTO logins
                    (email, rights, data, passwd, enabled, history,
                     service_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (self.email, json.dumps(self.rights), json.dumps(self.data),
                  self.passwd, getattr(self, 'enabled', 0),
                  json.dumps(self.history), self.service_hash))
        self.id = c.lastrowid
    except IntegrityError:
        return LOGIN_EXIST
    tran.commit()
# enddef


def _mod(self, c, keys, vals, condition=None):
    if condition is None:
        condition = ('login_id', self.id)
    if condition[0] not in ('login_id', 'email', 'service_hash'):
        raise AssertionError('Unsuported condition %s' % condition)

    try:        # email must be uniq
        if 'rights' in keys:        # transfer rights to string (driver depend)
            i = keys.index('rights')
            vals[i] = json.dumps(vals[i])

        if 'data' in keys or 'history' in keys:     # data will be merged
            c.execute("SELECT data, history FROM logins WHERE %s = %%s" %
                      condition[0], condition[1])
            row = c.fetchone()

        if 'data' in keys:
            i = keys.index('data')
            data = json.loads(row[0])

            data.update(vals[i])            # append / replace keys from vals
            for k, v in data.items():    # clean empty keys
                if isinstance(v, dict) and len(v) == 0:
                    data.pop(k)

            vals[i] = json.dumps(data)
        # endif

        if 'history' in keys:
            l = keys.index('history')
            history = json.loads(row[1])

            for it in vals[l]:              # append history from vals
                history.append(it)

            vals[l] = json.dumps(history)
        # endif

        keys = list('%s = %%s' % k for k in keys)
        vals.append(condition[1])
        c.execute("UPDATE logins SET %s WHERE %s = %%s " %
                  (', '.join(keys), condition[0]), vals)
    except IntegrityError:
        return LOGIN_EXIST

    if not c.rowcount:
        return LOGIN_NOT_EXIST
    return OK
# enddef


def enable(self, req):
    """Disabling account clear servis_hash."""
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    if not self.enabled:
        c.execute("""
                UPDATE logins SET enabled = %s, service_hash = NULL
                WHERE login_id = %s""", (self.enabled, self.id))
    else:
        c.execute("""
                UPDATE logins SET enabled = %s
                WHERE login_id = %s""", (self.enabled, self.id))

    if not c.rowcount:
        return LOGIN_NOT_EXIST

    tran.commit()
# enddef


def find(self, req):
    tran = req.db.transaction(req.logger)
    tran.connection.create_function('hash', 3, login_hash)
    c = tran.cursor()
    c.execute("""
        SELECT login_id, rights, data, history, hash(email, enabled, passwd)
        FROM logins WHERE email = %s AND passwd = %s AND enabled = 1
        """, (self.email, self.passwd))
    row = c.fetchone()
    tran.commit()

    if not row:
        return False
    self.id = row[0]
    self.rights = json.loads(row[1])
    self.data = json.loads(row[2])
    self.history = json.loads(row[3])
    self.md5 = row[4]
    return True
# enddef


def item_list(req, pager):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("""
        SELECT login_id, email, rights, enabled
        FROM logins ORDER BY email %s LIMIT %%d, %%d
        """ % pager.sort, (pager.offset, pager.limit))
    items = []
    for row in iter(c.fetchone, None):
        login = Login(row[0])
        login.email = row[1]
        login.rights = json.loads(row[2])
        login.enabled = row[3]
        items.append(login)
    # endfor

    c.execute("SELECT count(*) FROM logins")
    pager.total = c.fetchone()[0]
    tran.commit()

    return items
# enddef
