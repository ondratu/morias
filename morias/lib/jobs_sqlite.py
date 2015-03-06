
from datetime import datetime

import json

from sqlite3 import IntegrityError

from lib.jobs import Job

def get(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT path, timestamp, singleton, pid, login_id, data "
                "FROM jobs WHERE pid = %s OR path = %s", (self.pid, self.path))
    row = c.fetchone()
    if not row:
        return None

    self.path, timestamp, self.singleton, self.pid, self.login, data = row
    self.timestamp = datetime.fromtimestamp(timestamp)
    self.data = json.loads(data)
    return self
#enddef

def add(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    try:
        c.execute("INSERT INTO jobs "
                "(path, timestamp, singleton, pid, login_id, data) "
                "VALUES (%s, strftime('%%s','now')*1, %s, %d, %s, %s)",
                (self.path, self.singleton, self.pid, self.login_id,
                 json.dumps(self.data)) )
        tran.commit()
    except IntegrityError as e:
        return None
    return self
#enddef

def mod(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("UPDATE jobs SET data = %s WHERE pid = %d",
            (json.dumps(self.data), self.pid) )
    tran.commit()
#enddef

def delete(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("DELETE FROM jobs WHERE pid = %d", self.pid)
    tran.commit()
#enddef

def item_list(req, pager, **kwargs):
    keys = list( "%s %s %%s" % (k, 'in' if islistable(v) else '=') for k,v in kwargs.items() )
    cond = "WHERE " + ' AND '.join(keys) if keys else ''

    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT path, timestamp, singleton, pid, j.login_id, email, j.data "
            "FROM jobs j LEFT JOIN logins l ON (l.login_id = j.login_id) "
            "%s ORDER BY %s LIMIT %%d, %%d" % (cond, pager.order),
            tuple(kwargs.values()) + (pager.offset, pager.limit) )
    items = []
    for row in iter(c.fetchone, None):
        item = Job('')
        item.path, timestamp, item.singleton, item.pid, item.login_id, item.email, data = row
        item.timestamp = datetime.fromtimestamp(timestamp)
        item.data = json.loads(data)
        items.append(item)

    c.execute("SELECT count(*) FROM jobs %s" % cond, kwargs.values())
    pager.total, = c.fetchone()
    tran.commit()

    return items
#enddef
