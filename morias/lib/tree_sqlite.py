
from sqlite3 import IntegrityError
from falias.sqlite import DictCursor
from falias.util import islistable
from collections import OrderedDict

import json

from lib.tree import Item

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

# static method
def _get_item(c, cls, id = None, next = None):
    """ return item by id or next or last if both are None.
        Item is defined only by id, parent, nect and first value.
    """

    if id:
        cond = cls.ID + " = %s"
    else:
        cond = cls.NEXT + " " + ( 'is' if next is None else '=' ) + " %s"

    #cond = cls.ID +" = %s" if id else cls.NEXT+" = %s"
    c.execute("SELECT %s, %s, %s, %s FROM %s WHERE %s" % \
                    (cls.ID, cls.PARENT, cls.NEXT, cls.ORDER, cls.TABLE, cond),
              id if id else next)
    row = c.fetchone()
    if not row:
        return None
    item = cls(None)
    item.id, item.parent, item.next, item.order = row
    return item

# static method
def _fix_parent(c, cls, old_parent, new_parent):
    """ update parent for all old_parent's childs to be  new_parent's child """
    c.execute("UPDATE %s SET %s = %%s WHERE %s = %%s" % \
                (cls.TABLE, cls.PARENT, cls.PARENT), (new_parent, old_parent))


def _add(self, c, **kwargs):
    """ create item record in database """
    kwargs.update({self.PARENT: self.parent, self.NEXT: self.next, self.ORDER: self.order})
    try:
        c.execute("INSERT INTO %s (%s) VALUES (%s)" % \
            (self.TABLE, ','.join(kwargs.keys()), ','.join(['%s'] * len(kwargs))),
            kwargs.values())
        self.id = c.lastrowid
    except IntegrityError as e:
        raise KeyError("Some key exist yet or some reference not")


def _mod(self, c):
    """ store parent, next and first value to database """
    c.execute("UPDATE %s SET %s = %%s, %s = %%s, %s = %%s WHERE %s = %%s" % \
                (self.TABLE, self.PARENT, self.NEXT, self.ORDER, self.ID),
                (self.parent, self.next, self.order, self.id))
    if c.rowcount == 0:
        raise KeyError ("Item `%s' not found" % self.id)


def _get(self, c):
    """ load fresh tree info (parent, next, order) from database """
    c.execute("SELECT %s, %s, %s FROM %s WHERE %s = %%s" % \
            (self.PARENT, self.NEXT, self.ORDER, self.TABLE, self.ID),
            self.id)
    row = c.fetchone()
    if row is None:
        raise KeyError ("Item `%s' not found" % self.id)
    self.parent, self.next, self.order = row


def _del(self, c):
    """ delete item from table """
    c.execute("DELETE FROM %s WHERE %s = %%d" % (self.TABLE, self.ID), self.id)
    if not c.rowcount:
        raise KeyError ("Item `%s' not found" % self.id)


def get(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor(DictCursor)
    c.execute("SELECT * FROM %s WHERE %s = %%d" % (self.TABLE, self.ID), self.id)

    row = c.fetchone()
    if not row:
        return None
    self.parent = row[self.PARENT]
    self.next = row[self.NEXT]
    self.order = row[self.ORDER]
    tran.commit()
    return dict( (k, row[k]) for k in row.keys() )
#enddef

def mod(self, req, **kwargs):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    try:        # page name must be uniq
        c.execute("UPDATE %s SET %s WHERE %s = %%d" % \
                (self.TABLE, ','.join('%s=%%s' % key for key in kwargs.keys()), self.ID),
                kwargs.values() + [self.id])
    except IntegrityError as e:
        return False

    if not c.rowcount:
        return None

    tran.commit()
    return self
#enddef

# static method
def item_list(req, cls, pager, **kwargs):
    keys = list( "%s %s %%s" % (k, 'in' if islistable(v) else '=') for k,v in kwargs.items() )
    cond = "WHERE " + ' AND '.join(keys) if keys else ''

    tran = req.db.transaction(req.logger)
    c = tran.cursor(DictCursor)
    c.execute("SELECT * FROM %s %s ORDER BY %s LIMIT %%d, %%d" % \
                (cls.TABLE, cond, pager.order),
            tuple(kwargs.values()) + (pager.offset, pager.limit))
    items = []
    for row in iter(c.fetchone, None):
        items.append( dict((k, row[k]) for k in row.keys()) )
    #endwhile

    c.execute("SELECT count(*) FROM page_files")
    pager.total = c.fetchone()[0]
    tran.commit()

    return items
#enddef

#static method
def full_tree(req, cls, **kwargs):
    keys = list( "%s %s %%s" % (k, 'in' if islistable(v) else '=') for k,v in kwargs.items() )
    cond = "WHERE " + ' AND '.join(keys) if keys else ''

    tran = req.db.transaction(req.logger)
    c = tran.cursor(DictCursor)
    c.execute("SELECT * FROM %s %s ORDER BY %s" % \
                (cls.TABLE, cond, cls.ORDER), tuple(kwargs.values()))

    items = OrderedDict()
    for row in iter(c.fetchone, None):
        items[row[cls.ID]] = dict((k, row[k]) for k in row.keys())
    #endwhile
    tran.commit()

    return items
#enddef
