
import json

from sqlite3 import IntegrityError
from os.path import getmtime
from datetime import datetime
from falias.util import islistable

from lib.page_file import Page, PAGE_EXIST, PAGE_NOT_EXIST


def get(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("""
        SELECT author_id, name, title, locale, editor_rights
            FROM page_files WHERE page_id = %s
        """, self.id)
    row = c.fetchone()
    if not row:
        return None
    self.author_id, self.name, self.title, self.locale, rights = row
    self.rights = json.loads(rights)
    tran.commit()
    return self
# enddef


def add(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    try:        # page must be uniq
        c.execute("""
            INSERT INTO page_files
                    (author_id, name, title, locale, editor_rights)
                VALUES ( %s, %s, %s, %s, %s)
            """, (self.author_id, self.name, self.title, self.locale,
                  json.dumps(self.rights)))
        self.id = c.lastrowid
    except IntegrityError:
        return PAGE_EXIST

    self.save(req)
    tran.commit()
# enddef


def mod(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    try:        # page name must be uniq
        c.execute("""
            UPDATE page_files SET
                    name=%s, title=%s, locale=%s, editor_rights=%s
                WHERE page_id = %s
            """, (self.name, self.title, self.locale, json.dumps(self.rights),
                  self.id))
    except IntegrityError:
        return PAGE_EXIST

    if not c.rowcount:
        return PAGE_NOT_EXIST

    self.save(req)
    tran.commit()
# enddef


def delete(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("""
        SELECT author_id, name, title, locale, editor_rights
            FROM page_files WHERE page_id = %s
        """, self.id)
    self.author_id, self.name, self.title, self.locale, rights = c.fetchone()

    c.execute("DELETE FROM page_files WHERE page_id = %s", self.id)
    if not c.rowcount:
        return PAGE_NOT_EXIST

    # backup deleted file to history and remove target
    self.remove(req, rights)
    tran.commit()
# enddef


def load_rights(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("""
        SELECT author_id, editor_rights FROM page_files WHERE page_id = %s
        """, self.id)
    row = c.fetchone()
    if not row:
        self.author_id = None
        self.rights = ()
        return ()

    self.author_id, rights = row
    tran.commit()
    self.rights = json.loads(rights)
    return self.rights
# enddef


def regenerate_all(req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT page_id, author_id, name, title, locale FROM page_files")
    row = c.fetchone()
    while row is not None:
        page_id, author_id, name, title, locale = row
        page = Page(page_id)
        page.author_id = author_id
        page.name = name
        page.title = title
        page.locale = locale
        page.regenerate(req)
        row = c.fetchone()
    tran.commit()
# enddef


def item_list(req, pager, **kwargs):
    keys = list("%s %s %%s" % (k, 'in' if islistable(v) else '=')
                for k, v in kwargs.items())
    cond = "WHERE " + ' AND '.join(keys) if keys else ''

    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("""
        SELECT page_id, author_id, name, title, locale, editor_rights
            FROM page_files %s
                ORDER BY %s %s LIMIT %%s, %%s
        """ % (cond, pager.order, pager.sort),
              tuple(kwargs.values()) + (pager.offset, pager.limit))
    items = []
    for row in iter(c.fetchone, None):
        page_id, author_id, name, title, locale, editor_rights = row
        page = Page(page_id)
        page.author_id = author_id
        page.name = name
        page.title = title
        page.locale = locale
        page.rights = json.loads(editor_rights)
        page.modify = datetime.fromtimestamp(   # timestamp of last modify
            getmtime(req.cfg.pages_source + '/' + page.name))
        items.append(page)
    # endfow

    c.execute("SELECT count(*) FROM page_files %s" % cond, kwargs.values())
    pager.total = c.fetchone()[0]
    tran.commit()

    return items
# enddef
