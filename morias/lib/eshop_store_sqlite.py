
from falias.util import islistable
from sqlite3 import IntegrityError

import json

from lib.eshop_store import Item, Action, ACTION_INC, ACTION_DEC, ACTION_PRI
from lib.attachments import Attachment


def get(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("""
        SELECT modify_date, name, price, description, count, state, data,
            image_id, image_md5, image_mime_type
        FROM eshop_store WHERE item_id = %d""", self.id)
    row = c.fetchone()
    if not row:
        return None

    tran.commit()
    self.modify_date, self.name, self.price, self.description, self.count, \
        self.state, data, self.image_id, self.image_md5, \
        self.image_mime_type = row
    if self.image_id:
        self.image = Attachment(self.image_id,
                                self.image_md5,
                                self.image_mime_type)
    self.data = json.loads(data)
    return self
# enddef


def add(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    c.execute("""
        INSERT INTO eshop_store
                (modify_date, name, description, state, data)
            VALUES (strftime('%%s','now')*1, %s, %s, %d, %s)
            """, (self.name, self.description, self.state,
                  json.dumps(self.data)))
    self.id = c.lastrowid
    tran.commit()
    return self
# enddef


def mod(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    c.execute("""
        UPDATE eshop_store SET
                modify_date=strftime('%%s','now')*1, name=%s,
                description = %s, state = %d, data = %s
        WHERE item_id = %d
        """, (self.name, self.description, self.state, json.dumps(self.data),
              self.id))

    if not c.rowcount:
        return None
    tran.commit()
    return self
# enddef


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
# enddef


def _action(self, c, action):
    c.execute("""
        INSERT INTO eshop_store_action
                (item_id, timestamp, action_type, data)
            VALUES (%d, strftime('%%s','now')*1, %d, %s)
        """, (self.id, action.action_type, json.dumps(action.data)))
    if action.action_type == ACTION_INC:
        try:
            c.execute("""
                UPDATE eshop_store SET count=count + %d,
                        modify_date=strftime('%%s','now')*1
                    WHERE item_id = %d
                """, (action.data['count'], self.id))
        except IntegrityError as e:
            if e.message.startswith('@less_then_zero:'):
                raise ValueError(e.message[17:], self.id)   # must be user like
            raise e
    elif action.action_type == ACTION_DEC:
        try:
            c.execute("""
                UPDATE eshop_store SET count=count - %d,
                        modify_date=strftime('%%s','now')*1
                    WHERE item_id = %d
                """, (action.data['count'], self.id))
        except IntegrityError as e:
            if e.message.startswith('@less_then_zero:'):
                raise ValueError(e.message[17:], self.id)   # must be user like
            raise e
    elif action.action_type == ACTION_PRI:
        c.execute("""
            UPDATE eshop_store SET price=%f,
                    modify_date=strftime('%%s','now')*1
                WHERE item_id = %d
            """, (action.data['price'], self.id))
        if not c.rowcount:
            return None
    else:
        raise RuntimeError("Unknown action_type")
    return self
# enddef


def action(self, req, action):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    rv = _action(self, c, action)
    tran.commit()
    return rv
# enddef


def item_list(req, pager, **kwargs):
    keys = list("%s %s %%s" % (k, 'in' if islistable(v) else '=')
                for k, v in kwargs.items())
    cond = "WHERE " + ' AND '.join(keys) if keys else ''

    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("""
        SELECT item_id, modify_date, name, price, description, count,
                state, data, image_id, image_md5, image_mime_type
        FROM eshop_store %s ORDER BY %s %s LIMIT %%s, %%s
        """ % (cond, pager.order, pager.sort),
              tuple(kwargs.values()) + (pager.offset, pager.limit))
    items = []
    for row in iter(c.fetchone, None):
        item = Item()
        item.id, item.modify_date, item.name, item.price, item.description, \
            item.count, item.state, data, \
            item.image_id, item.image_md5, item.image_mime_type = row
        item.data = json.loads(data)
        if item.image_id:       # create Attachment object if item_id was set
            item.image = Attachment(item.image_id,
                                    item.image_md5,
                                    item.image_mime_type)
        items.append(item)
    # endfor

    c.execute("SELECT count(*) FROM eshop_store %s" % cond, kwargs.values())
    pager.total = c.fetchone()[0]
    tran.commit()

    return items
# enddef


def item_list_actions(req, pager, **kwargs):
    keys = list("%s %s %%s" % (k, 'in' if islistable(v) else '=')
                for k, v in kwargs.items())
    cond = "WHERE " + ' AND '.join(keys) if keys else ''

    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("""
        SELECT item_id, timestamp, action_type, data
        FROM eshop_store_action %s ORDER BY %s %s LIMIT %%s, %%s
        """ % (cond, pager.order, pager.sort),
              tuple(kwargs.values()) + (pager.offset, pager.limit))

    items = []
    for row in iter(c.fetchone, None):
        item = Action()
        item.item_id, item.timestamp, item.action_type, data = row
        item.data = json.loads(data)
        items.append(item)
    return items
# enddef
