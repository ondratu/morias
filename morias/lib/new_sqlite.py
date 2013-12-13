
from datetime import datetime

from falias.util import uni, islistable

#errors
EMPTY_TITLE     = 1
EMPTY_BODY      = 2
NEW_NOT_EXIST   = 3

class New():
    def __init__(self, id = None):
        self.id = id

    def get(self, req):
        tran = req.db.transaction(req.logger)
        c = tran.cursor()
        c.execute("SELECT title, locale, create_date, body "
                        "FROM new WHERE new_id = %s", self.id)
        row = c.fetchone()
        if not row:
            return NEW_NOT_EXIST

        self.title, self.locale, create_date, self.body = row
        self.create_date = datetime.fromtimestamp(create_date)
        tran.commit()
    #enddef
    
    def add(self, req):
        if not self.title: return EMPTY_TITLE
        if not self.body: return EMPTY_BODY

        tran = req.db.transaction(req.logger)
        c = tran.cursor()

        c.execute("INSERT INTO new (title, locale, create_date, body) "
                    "VALUES ( %s, %s, strftime('%%s','now')*1, %s )",
                    (self.title, self.locale, self.body))
        self.id = c.lastrowid       
        tran.commit()
    #enddef

    def mod(self, req):
        if not self.title: return EMPTY_TITLE
        if not self.body: return EMPTY_BODY

        tran = req.db.transaction(req.logger)
        c = tran.cursor()
        
        c.execute("UPDATE new SET "
                        "title = %s, locale = %s, body = %s "
                    "WHERE new_id = %s",
                    (self.title, self.locale, self.body, self.id))
        
        if not c.rowcount:
            return NEW_NOT_EXIST
        tran.commit()
    #enddef

    def enable(self, req):
        tran = req.db.transaction(req.logger)
        c = tran.cursor()

        c.execute("UPDATE new SET enabled = %s WHERE new_id = %s",
                        (self.enabled, self.id))
        
        if not c.rowcount:
            return NEW_NOT_EXIST

        tran.commit()
    #enddef

    def bind(self, form):
        self.id = form.getfirst('new_id', fce = int) if 'new_id' in form else None
        self.title = form.getfirst('title', '', uni)
        self.locale = form.getfirst('locale', '', uni)
        self.body = form.getfirst('body', '', uni)
    #enddef

    @staticmethod
    def list(req, pager, body = False, **kwargs):
        if pager.order not in ('create_date', 'title', 'locale'):
            pager.order = 'create_date'

        body = ',body ' if body else ''

        keys = list( "%s %s %%s" % (k, 'in' if islistable(v) else '=') for k,v in kwargs.items() )
        cond = "WHERE " + ' AND '.join(keys) if keys else '' 

        tran = req.db.transaction(req.logger)
        c = tran.cursor()
        c.execute("SELECT new_id, enabled, create_date, title, locale %s"
                    "FROM new %s ORDER BY %s %s LIMIT %%s, %%s" % \
                        (body, cond, pager.order, pager.sort),
                    tuple(kwargs.values()) + (pager.offset, pager.limit))
        items = []
        row = c.fetchone()
        while row is not None:
            item = New(row[0])
            item.enabled = row[1]
            item.create_date = datetime.fromtimestamp(row[2])
            item.title = row[3]
            item.locale = row[4]
            if body:
                item.body = row[5]
            items.append(item)
            row = c.fetchone()
        #endwhile

        c.execute("SELECT count(*) FROM new %s" % cond, kwargs.values())
        pager.total = c.fetchone()[0]
        tran.commit()

        return items
    #enddef
#endclass
