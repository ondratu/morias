
from datetime import datetime
from falias.util import islistable
from falias.sqlite import DictCursor

import json

from lib.new import New

def get(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor(DictCursor)
    c.execute("SELECT author_id, title, locale, create_date, public_date, "
                    "body, state, data "
                "FROM news WHERE new_id = %s", self.id)
    row = c.fetchone()
    if not row:
        return None

    self.author_id = row['author_id']
    self.title = row['title']
    self.locale = row['locale']
    self.body = row['body']
    self.state = row['state']
    self.create_date = datetime.fromtimestamp(row['create_date'])
    self.public_date = datetime.fromtimestamp(row['public_date'])
    self.data = json.loads(row['data'])
    tran.commit()
    return self
#enddef

def add(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    if self.public:
        c.execute("INSERT INTO news "
                "(author_id, title, locale, create_date, public_date, body, "
                        "state, data) "
            "VALUES (%s, %s, %s, strftime('%%s','now')*1, strftime('%%s','now')*1, "
                        "%s, %s, %s)",
                (self.author_id, self.title, self.locale, self.body, self.state,
                 json.dumps(self.data)))
    else:
        c.execute("INSERT INTO news "
                "(author_id, title, locale, create_date, body, state, data) "
            "VALUES (%s, %s, %s, strftime('%%s','now')*1, %s, %s, %s)",
                (self.author_id, self.title, self.locale, self.body, self.state,
                 json.dumps(self.data)))
    self.id = c.lastrowid
    tran.commit()
#enddef

def mod(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    if self.public:
        c.execute("UPDATE news SET "
                    "title = %s, locale = %s, body = %s, state = %s, data = %s, "
                    "public_date = strftime('%%s','now')*1 "
                "WHERE new_id = %s",
                (self.title, self.locale, self.body, self.state,
                 json.dumps(self.data), self.id))
    else:
        c.execute("UPDATE news SET "
                    "title = %s, locale = %s, body = %s, state = %s, data = %s "
                "WHERE new_id = %s",
                (self.title, self.locale, self.body, self.state,
                 json.dumps(self.data), self.id))

    if not c.rowcount:
        return None
    tran.commit()
    return self
#enddef

def set_state(self, req, state):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    c.execute("UPDATE news SET state = %s WHERE new_id = %s",
                    (state, self.id))

    if not c.rowcount:
        return None

    tran.commit()
    self.state = state
    return self
#enddef

def item_list(req, pager, body, **kwargs):
    body = ',body ' if body else ''

    public = kwargs.pop('public', False)
    keys = list( "%s %s %%s" % (k, 'in' if islistable(v) else '=') for k,v in kwargs.items() )
    if public:       # public is alias key
        keys.append("public_date > 0")
        keys.append("state != 0")

    cond = "WHERE " + ' AND '.join(keys) if keys else ''

    tran = req.db.transaction(req.logger)
    c = tran.cursor(DictCursor)
    c.execute("SELECT new_id, author_id, email, state, create_date, public_date, title, "
                        "locale, state %s"
                "FROM news n LEFT JOIN logins l ON (n.author_id = l.login_id) %s "
                    "ORDER BY %s %s LIMIT %%s, %%s" % \
                    (body, cond, pager.order, pager.sort),
                tuple(kwargs.values()) + (pager.offset, pager.limit))
    items = []
    row = c.fetchone()
    while row is not None:
        item = New(row['new_id'])
        item.author_id = row['author_id']
        item.author = row['email']
        item.state = row['state']
        item.create_date = datetime.fromtimestamp(row['create_date'])
        item.public_date = datetime.fromtimestamp(row['public_date'])
        item.title = row['title']
        item.locale = row['locale']
        if body:
            item.body = row['body']
        items.append(item)
        row = c.fetchone()
    #endwhile

    c.execute("SELECT count(*) FROM news %s" % cond, kwargs.values())
    pager.total = c.fetchone()['count(*)']
    tran.commit()

    return items
#enddef
