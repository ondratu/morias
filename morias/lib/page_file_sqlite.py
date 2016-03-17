from sqlite3 import IntegrityError
from falias.util import islistable
from falias.sqlite import DictCursor

from os.path import getmtime
from datetime import datetime

import json

from morias.lib.page_file import Page, PAGE_EXIST, PAGE_NOT_EXIST


def test(req):
    with req.db.transaction(req.log_info) as c:
        c.execute("PRAGMA stats")
        c.execute("SELECT strftime('%s','2013-12-09 18:19')*1")
        value = c.fetchone()[0]
        assert value == 1386613140
        c.execute("""
            SELECT author_id, name, title, locale, editor_rights, format
                FROM page_files LIMIT 1
            """)


def get(self, req):
    tran = req.db.transaction(req.log_info)
    c = tran.cursor(DictCursor)
    c.execute("""
        SELECT author_id, name, title, locale, editor_rights, format
            FROM page_files WHERE page_id = %s
        """, self.id)
    row = c.fetchone()
    if not row:
        return None
    self.from_row(row)
    tran.commit()
    return self
# enddef


def add(self, req):
    tran = req.db.transaction(req.log_info)
    c = tran.cursor()

    try:        # page must be uniq
        c.execute("""
            INSERT INTO page_files
                    (author_id, name, title, locale, editor_rights, format)
                VALUES ( %s, %s, %s, %s, %s)
            """, (self.author_id, self.name, self.title, self.locale,
                  json.dumps(self.rights), self.format))
        self.id = c.lastrowid
    except IntegrityError:
        return PAGE_EXIST

    self.save(req)
    tran.commit()
# enddef


def mod(self, req):
    tran = req.db.transaction(req.log_info)
    c = tran.cursor()

    try:        # page name must be uniq
        c.execute("""
            UPDATE page_files SET
                    name=%s, title=%s, locale=%s, editor_rights=%s, format=%d
                WHERE page_id = %s
            """, (self.name, self.title, self.locale, json.dumps(self.rights),
                  self.format, self.id))
    except IntegrityError:
        return PAGE_EXIST

    if not c.rowcount:
        return PAGE_NOT_EXIST

    self.save(req)
    tran.commit()
# enddef


def delete(self, req):
    tran = req.db.transaction(req.log_info)
    c = tran.cursor(DictCursor)
    c.execute("""
        SELECT author_id, name, title, locale, editor_rights, format
            FROM page_files WHERE page_id = %s
        """, self.id)
    self.from_row(c.fetchone())

    c.execute("DELETE FROM page_files WHERE page_id = %s", self.id)
    if not c.rowcount:
        return PAGE_NOT_EXIST

    # backup deleted file to history and remove target
    self.remove(req)
    tran.commit()
# enddef


def load_rights(self, req):
    tran = req.db.transaction(req.log_info)
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
    tran = req.db.transaction(req.log_info)
    c = tran.cursor()
    c.execute("""
        SELECT page_id, author_id, name, title, locale, format
        FROM page_files
        """)
    for row in iter(c.fetchone, None):
        page = Page()
        page.from_row(row)
        page.regenerate(req)
    tran.commit()
# enddef


def item_list(req, pager, **kwargs):
    keys = list("%s %s %%s" % (k, 'in' if islistable(v) else '=')
                for k, v in kwargs.items())
    cond = "WHERE " + ' AND '.join(keys) if keys else ''

    tran = req.db.transaction(req.log_info)
    c = tran.cursor(DictCursor)
    c.execute("""
        SELECT page_id, author_id, name, title, locale, editor_rights, format
            FROM page_files %s
                ORDER BY %s %s LIMIT %%s, %%s
        """ % (cond, pager.order, pager.sort),
              tuple(kwargs.values()) + (pager.offset, pager.limit))
    items = []
    for row in iter(c.fetchone, None):
        page = Page()
        page.from_row(row)
        page.modify = datetime.fromtimestamp(   # timestamp of last modify
            getmtime(req.cfg.pages_source + '/' + page.name))
        items.append(page)
    # endfow

    c.execute("SELECT count(*) FROM page_files %s" % cond, kwargs.values())
    pager.total = c.fetchone()[0]
    tran.commit()

    return items
# enddef
