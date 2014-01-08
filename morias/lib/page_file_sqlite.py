
import json

from sqlite3 import IntegrityError
from os.path import getmtime
from datetime import datetime

from lib.page_file import Page, PAGE_EXIST, PAGE_NOT_EXIST 

def get(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT name, title, locale, editor_rights "
                "FROM page WHERE page_id = %s", self.id)
    self.name, self.title, self.locale, rights = c.fetchone()
    self.rights = json.loads(rights)
    tran.commit()
#enddef

def add(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    try:        # page must be uniq
        c.execute("INSERT INTO page (name, title, locale, editor_rights) "
                    "VALUES ( %s, %s, %s, %s )",
                (self.name, self.title, self.locale, json.dumps(self.rights)))
        self.id = c.lastrowid
    except IntegrityError as e:
        return PAGE_EXIST

    self.save(req)

    tran.commit()
#enddef

def mod(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    try:        # page name must be uniq
        c.execute("UPDATE page SET "
                    "name = %s, title = %s, locale = %s, editor_rights = %s "
                "WHERE page_id = %s",
                (self.name, self.title, self.locale, json.dumps(self.rights), self.id))
    except IntegrityError as e:
        return PAGE_EXIST

    if not c.rowcount:
        return PAGE_NOT_EXIST

    self.save(req)

    tran.commit()
#enddef

def delete(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT name, title, locale, editor_rights "
                "FROM page WHERE page_id = %s", self.id)
    self.name, self.title, self.locale, rights = c.fetchone()

    c.execute("DELETE FROM page WHERE page_id = %s", self.id)

    if not c.rowcount:
        return PAGE_NOT_EXIST
        
    self.remove(req, rights) # backup deleted file to history and remove target

    tran.commit()
#enddef

def load_rights(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT editor_rights FROM page WHERE page_id = %s", self.id)

    rights = json.loads(c.fetchone()[0])
    return rights
#enddef

def regenerate_all(req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT page_id, name, title, locale FROM page")
    items = []
    row = c.fetchone()
    while row is not None:
        page = Page(row[0])
        page.name = row[1]
        page.title = row[2]
        page.locale = row[3]
        page.regenerate(req)            
        row = c.fetchone()

    tran.commit()
#enddef

def item_list(req, pager):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT page_id, name, title, locale, editor_rights "
                "FROM page ORDER BY name LIMIT %s, %s",
                (pager.offset, pager.limit))
    items = []
    row = c.fetchone()
    while row is not None:
        page = Page(row[0])
        page.name = row[1]
        page.title = row[2]
        page.locale = row[3]
        page.rights = json.loads(row[4])
        page.modify = datetime.fromtimestamp(   # timestamp of last modify
                        getmtime(req.cfg.pages_source + '/' + page.name))
        items.append(page)
        row = c.fetchone()
    #endwhile

    c.execute("SELECT count(*) FROM page")
    pager.total = c.fetchone()[0]
    tran.commit()

    return items
#enddef
