
from falias.util import islistable

def get(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT value FROM options WHERE section = %s AND option = %s",
                (self.section, self.option))
    row = c.fetchone()
    if not row:
        return None

    tran.commit()
    self.value = row[0]
    return self
#enddef

def add(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("INSERT INTO options (section, option, value) "
                "VALUES (%s, %s, %s)", (self.section, self.option, self.value))
    tran.commit()
    return self
#enddef

def mod(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("UPDATE options SET value = %s", self.value)
    if not c.rowcount:
        return None
    tran.commit()
    return self
#enddef

def option_set(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("INSERT OR REPLACE INTO options (section, option, value) "
                "VALUES (%s, %s, %s)", (self.section, self.option, self.value))
    tran.commit()
    return self
#enddef

def delete(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("DELETE FROM options WHERE section = %s AND option = %s",
            (self.section, self.option))
    tran.commit()
#enddef

def options_list(req, pager, **kwargs):
    keys = list( "%s %s %%s" % (k, 'in' if islistable(v) else '=') for k,v in kwargs.items() )
    cond = "WHERE " + ' AND '.join(keys) if keys else ''

    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT section, option, value FROM options %s "
            "ORDER BY %s %s LIMIT %%s, %%s" % (cond, pager.order, pager.sort),
            tuple(kwargs.values()) + (pager.offset, pager.limit))
    items = []
    for row in iter(c.fetchone, None):
        item = Option()
        item.section, item.option, item.value = row
        items.append(item)
    #endfor

    c.execute("SELECT count(*) FROM options %s" % cond, kwargs.values())
    pager.total = c.fetchone()[0]
    tran.commit()

    return items
#enddef
