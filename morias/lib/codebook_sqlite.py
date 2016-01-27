from falias.sqlite import DictCursor
from sqlite3 import IntegrityError


def get(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor(DictCursor)
    c.execute("SELECT * FROM %s WHERE %s = %%d" % (self.TABLE, self.ID),
              self.id)

    row = c.fetchone()
    if not row:
        return None
    tran.commit()
    return dict((k, row[k]) for k in row.keys())


def add(self, req, **kwargs):
    """ create item record in database """
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    try:
        c.execute("INSERT INTO %s (%s) VALUES (%s)" %
                  (self.TABLE, ','.join(kwargs.keys()),
                   ','.join(['%s'] * len(kwargs))), kwargs.values())
        self.id = c.lastrowid
    except IntegrityError:
        req.log_error("Some key exist yet or some reference not")
        return None
    tran.commit()
    return self


def mod(self, req, **kwargs):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    try:        # value could be uniq
        c.execute("UPDATE %s SET %s WHERE %s = %%d" %
                  (self.TABLE,
                   ','.join('%s=%%s' % key for key in kwargs.keys()), self.ID),
                  kwargs.values() + [self.id])
    except IntegrityError:
        return False

    if not c.rowcount:
        return None

    tran.commit()
    return self
# enddef


def delete(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    try:    # value could be used
        c.execute("DELETE FROM %s WHERE %s = %%d" %
                  (self.TABLE, self.ID), self.id)
    except IntegrityError:
        return False
    tran.commit()
    return True
# enddef


def item_list(req, cls, pager, search=None):   # static method
    order = pager.order
    if order == 'id':
        order = cls.ID
    elif order == 'value':
        order = cls.VALUE

    cond = ''
    if search:
        cond = "WHERE {0} LIKE '%%{1}%%'".format(cls.VALUE, search)

    tran = req.db.transaction(req.logger)
    c = tran.cursor(DictCursor)
    c.execute("SELECT * FROM %s %s ORDER BY %s %s LIMIT %%d, %%d" %
              (cls.TABLE, cond, order, pager.sort),
              (pager.offset, pager.limit))
    items = []
    for row in iter(c.fetchone, None):
        attrs = dict((k, row[k]) for k in row.keys())
        attrs['id'] = attrs.pop(cls.ID)         # rename to Item default names
        attrs['value'] = attrs.pop(cls.VALUE)
        items.append(cls(**attrs))

    c.execute("SELECT count(*) FROM %s %s" % (cls.TABLE, cond))
    pager.total = c.fetchone()[0]
    tran.commit()

    return items
# enddef
