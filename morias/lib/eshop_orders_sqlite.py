
from falias.util import Object, islistable

import json

from lib.eshop_orders import Order

# static method
def _lock(req):
    """ lock database for any read/write operatios """
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute('BEGIN EXCLUSIVE TRANSACTION')
    return c

# static method
def _commit(c):
    c.transaction.commit()

#static method
def _rollback(c):
    c.transaction.rollback()

def _get(self, c):
    c.execute("SELECT client_id, email, create_date, modify_date, state, items, "
                    "history, data FROM eshop_orders WHERE order_id = %d", self.id)
    row = c.fetchone()
    if not row:
        return None

    self.client_id, self.email, self.create_date, self.modify_date, \
            self.state, items, history, data = row
    self.items = json.loads(items)
    self.history = json.loads(history)
    self.data = json.loads(data)

    return self
#enddef

def get(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    if _get(self, c) is None:
        return None
    tran.commit()
    return self
#enddef

def _add (self, c):
    c.execute("INSERT INTO eshop_orders (client_id, email, create_date, "
                    "modify_date, state, items, history, data) "
                "VALUES (%s, %s, strftime('%%s','now')*1, strftime('%%s','now')*1, "
                    "%d, %s, %s, %s)",
                (self.client_id, self.email, self.state, json.dumps(self.items),
                 json.dumps(self.history), json.dumps(self.data) ) )
    c.execute("SELECT order_id, create_date FROM eshop_orders WHERE rowid = %d",
                c.lastrowid)
    self.id, self.create_date = c.fetchone()
#enddef

def _mod(self, c):
    c.execute("UPDATE eshop_orders SET "
                "email = %s, modify_date = strftime('%%s','now')*1, state = %d, "
                "items = %s, history = %s, data = %s "
            "WHERE order_id = %d",
                (self.email, self.state, json.dumps(self.items),
                 json.dumps(self.history), json.dumps(self.data), self.id) )
    if not c.rowcount:
        return None
    return self
#enddef

def mod(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    if self._mod(c) is None:
        return None
    tran.commit()
    return self
#enddef

# static method
def item_list(req, pager, **kwargs):
    client = kwargs.pop('client') if 'client' in kwargs else None
    keys = list( "%s %s %%s" % ('o.'+k, 'in' if islistable(v) else '=') for k,v in kwargs.items() )
    cond = "WHERE " + ' AND '.join(keys) if keys else ''
    if client:      # client have special OR mod
        cond = cond + ' AND ' if cond else "WHERE "
        cond += "(o.email = %s OR c.email = %s)"
        kwargs['o.email'] = client
        kwargs['c.email'] = client

    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT o.order_id, o.client_id, c.email, o.email, o.create_date, "
                    "o.modify_date, o.state "
                "FROM eshop_orders o LEFT JOIN logins c ON (o.client_id = c.login_id) "
                "%s ORDER BY %s %s LIMIT %%s, %%s" % \
                (cond, pager.order, pager.sort),
                tuple(kwargs.values()) + (pager.offset, pager.limit))
    items = []
    for row in iter(c.fetchone, None):
        item = Object()
        item.id, item.client_id, item.client, item.email, item.create_date, \
                item.modify_date, item.state = row
        items.append(item)
    #endfor

    c.execute("SELECT count(*) FROM eshop_orders o "
                "LEFT JOIN logins c ON (o.client_id = c.login_id) %s" \
                % cond, kwargs.values())
    pager.total = c.fetchone()[0]
    tran.commit()

    return items
#enddef
