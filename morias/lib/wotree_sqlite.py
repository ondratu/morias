from sqlite3 import IntegrityError
from falias.sqlite import DictCursor
from falias.util import islistable


def _lock(req):     # static method
    """ lock database for any read/write operatios """
    tran = req.db.transaction(req.log_info)
    c = tran.cursor()
    c.execute('BEGIN EXCLUSIVE TRANSACTION')
    return c


def _commit(c):     # static method
    c.transaction.commit()


def _rollback(c):   # static method
    c.transaction.rollback()


def _add(self, c, **kwargs):
    """ create item record in database """
    kwargs.update({self.ID: self.id})
    try:
        c.execute("INSERT INTO %s (%s) VALUES (%s)" %
                  (self.TABLE, ','.join(kwargs.keys()),
                   ','.join(['%s'] * len(kwargs))), kwargs.values())
    except IntegrityError as e:
        raise KeyError(e)


def get(self, req, **cond):
    cond.update({self.ID: self.id})
    tran = req.db.transaction(req.log_info)
    c = tran.cursor(DictCursor)
    c.execute("SELECT * FROM %s WHERE %s" %
              (self.TABLE,
               ' AND '.join('%s=%%s' % key for key in cond.keys())),
              (cond.values()))

    row = c.fetchone()
    if not row:
        return None
    tran.commit()
    return dict((k, row[k]) for k in row.keys())
# enddef


def mod(self, req, **kwargs):
    cond = kwargs.pop('__cond__', {})
    cond.update({self.ID: self.id})

    tran = req.db.transaction(req.log_info)
    c = tran.cursor()

    try:        # page name must be uniq
        c.execute("UPDATE %s SET %s WHERE %s" %
                  (self.TABLE,
                   ','.join('%s=%%s' % key for key in kwargs.keys()),
                   ' AND '.join('%s=%%s' % key for key in cond.keys())),
                  kwargs.values() + cond.values())
    except IntegrityError:
        return False

    if not c.rowcount:
        return None

    tran.commit()
    return self
# enddef


def item_list(req, cls, pager, **kwargs):   # static method
    group_by = kwargs.pop('group_by', '')
    if group_by:
        group_by = "GROUP BY %s" % group_by
    keys = list("%s %s %%s" % (k, 'in' if islistable(v) else '=')
                for k, v in kwargs.items())
    cond = "WHERE " + ' AND '.join(keys) if keys else ''

    tran = req.db.transaction(req.log_info)
    c = tran.cursor(DictCursor)
    c.execute("SELECT * FROM %s %s %s ORDER BY %s %s LIMIT %%d, %%d" %
              (cls.TABLE, cond, group_by, pager.order, pager.sort),
              tuple(kwargs.values()) + (pager.offset, pager.limit))
    items = []
    for row in iter(c.fetchone, None):
        items.append(dict((k, row[k]) for k in row.keys()))

    c.execute("SELECT count(*) FROM %s %s" % (cls.TABLE, cond),
              kwargs.values())
    pager.total = c.fetchone()[0]
    tran.commit()

    return items
# enddef


def _last(c, cls, parent, **kwargs):
    keys = list("%s %s %%s" % (k, 'in' if islistable(v) else '=')
                for k, v in kwargs.items())
    keys.append('%s LIKE %%s' % cls.ID)
    cond = "WHERE " + ' AND '.join(keys) if keys else ''
    kwargs['parent'] = parent+'%'

    c.execute('SELECT %s FROM %s %s ORDER BY %s DESC LIMIT 1' %
              (cls.ID, cls.TABLE, cond, cls.ID), kwargs.values())
    row = c.fetchone()
    return row[0] if row else ''
