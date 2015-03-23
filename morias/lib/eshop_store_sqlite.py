
from falias.util import islistable

import json

from lib.eshop_store import Item, Action, ACTION_INC, ACTION_DEC, ACTION_PRI

def get(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT modify_date, name, price, description, count, state, data "
                "FROM eshop_store WHERE item_id = %d", self.id)
    row = c.fetchone()
    if not row:
        return None

    tran.commit()
    self.modify_date, self.name, self.price, self.description, self.count, \
            self.state, data = row
    self.data = json.loads(data)
    return self
#enddef

def add(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    c.execute("INSERT INTO eshop_store (modify_date, name, description, state, "
                    "data) "
                "VALUES (strftime('%%s','now')*1, %s, %s, %d, %s)",
                (self.name, self.description, self.state, json.dumps(self.data)) )
    self.id = c.lastrowid
    tran.commit()
    return self
#enddef

def mod(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    c.execute("UPDATE eshop_store SET "
                "modify_date = strftime('%%s','now')*1, name = %s, "
                "description = %s, state = %d, data = %s "
            "WHERE item_id = %d",
                (self.name, self.description, self.state, json.dumps(self.data),
                 self.id) )

    if not c.rowcount:
        return None
    tran.commit()
    return self
#enddef

def set_state(self, req, state):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    c.execute("UPDATE eshop_store SET state = %d WHERE item_id = %d",
                    (state, self.id))

    if not c.rowcount:
        return None

    tran.commit()
    self.state = state
    return self
#enddef


def action(self, req, action):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    c.execute("INSERT INTO eshop_store_action "
                    "(item_id, timestamp, action_type, data) "
                "VALUES (%d, strftime('%%s','now')*1, %d, %s)",
                (self.id, action.action_type, json.dumps(action.data)) )
    if action.action_type == ACTION_INC:
        c.execute("UPDATE eshop_store SET count = count + %d, "
                    "modify_date = strftime('%%s','now')*1 WHERE item_id = %d",
                    (action.data['count'], self.id))
    elif action.action_type == ACTION_DEC:
        c.execute("UPDATE eshop_store SET count = count - %d, "
                    "modify_date = strftime('%%s','now')*1 WHERE item_id = %d",
                    (action.data['count'], self.id))
    elif action.action_type == ACTION_PRI:
        c.execute("UPDATE eshop_store SET price = %f, "
                    "modify_date = strftime('%%s','now')*1 WHERE item_id = %d",
                    (action.data['price'], self.id))
        if not c.rowcount:
            return None
    else:
        raise RuntimeError("Unknown action_type")

    tran.commit()
    return self
#enddef

def item_list(req, pager, **kwargs):
    keys = list( "%s %s %%s" % (k, 'in' if islistable(v) else '=') for k,v in kwargs.items() )
    cond = "WHERE " + ' AND '.join(keys) if keys else ''

    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT item_id, modify_date, name, price, description, count, "
                    "state, data "
                "FROM eshop_store %s ORDER BY %s %s LIMIT %%s, %%s" % \
                (cond, pager.order, pager.sort),
                tuple(kwargs.values()) + (pager.offset, pager.limit))
    items = []
    for row in iter(c.fetchone, None):
        item = Item()
        item.id, item.modify_date, item.name, item.price, item.description, \
                item.count, item.state, data = row
        item.data = json.loads(data)
        items.append(item)
    #endwhile

    c.execute("SELECT count(*) FROM eshop_store %s" % cond, kwargs.values())
    pager.total = c.fetchone()[0]
    tran.commit()

    return items
#enddef

def item_list_actions(req, pager, **kwargs):
    keys = list( "%s %s %%s" % (k, 'in' if islistable(v) else '=') for k,v in kwargs.items() )
    cond = "WHERE " + ' AND '.join(keys) if keys else ''

    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT item_id, timestamp, action_type, data "
            "FROM eshop_store_action %s ORDER BY %s %s LIMIT %%s, %%s" % \
            (cond, pager.order, pager.sort),
            tuple(kwargs.values()) + (pager.offset, pager.limit) )

    items = []
    for row in iter(c.fetchone, None):
        item = Action()
        item.item_id, item.timestamp, item.action_type, data = row
        item.data = json.loads(data)
        items.append(item)
    #endwhile

    return items
