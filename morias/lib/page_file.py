
import json, re

from sqlite3 import IntegrityError
from os import rename, remove
from os.path import getmtime, exists
from datetime import datetime
from shutil import copyfile

from falias.util import uni

from core.render import generate_page
from core.login import match_right

#errors
EMPTY_FILENAME  = 1
BAD_FILENAME    = 2
PAGE_EXIST      = 3
PAGE_NOT_EXIST  = 4

re_filename = re.compile(r"^[\w\.-]+\.html$")

class Page():
    def __init__(self, id = None):
        self.id = id

    def get(self, req):
        tran = req.db.transaction(req.logger)
        c = tran.cursor()
        c.execute("SELECT name, title, locale, editor_rights "
                    "FROM page WHERE page_id = %s", self.id)
        self.name, self.title, self.locale, rights = c.fetchone()
        self.rights = json.loads(rights)
        tran.commit()

        with open (req.cfg.pages_source + '/' + self.name, 'r') as f:
            self.text = f.read().decode('utf-8')
    #enddef

    def add(self, req):
        if not self.name: return EMPTY_FILENAME

        if not self.check_filename(): return BAD_FILENAME

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
        if not self.name: return EMPTY_FILENAME

        if not self.check_filename(): return BAD_FILENAME

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

        # meta file about deleted page
        backup = req.cfg.pages_history + '/' + self.name
        with open (backup + '.' + datetime.now().isoformat() + '.deleted' , 'w+') as tmp:
            tmp.write("title: %s\n" % self.title)
            tmp.write("locale: %s\n" % self.locale)
            tmp.write("editor_rights: %s\n" % rights)

        c.execute("DELETE FROM page WHERE page_id = %s", self.id)

        if not c.rowcount:
            return PAGE_NOT_EXIST

        # simple backup deleted file to history
        source = req.cfg.pages_source + '/' + self.name
        if exists(source):      # backup old file
            backup = req.cfg.pages_history + '/' + self.name
            rename(source, backup + '.' + datetime.now().isoformat())

        target = req.cfg.pages_out + '/' + self.name
        if exists(target):      # delete output file
            remove(target)

        tran.commit()
    #enddef

    def bind(self, form):
        self.id = form.getfirst('page_id', fce = int) if 'page_id' in form else None
        self.name = form.getfirst('name', '', uni)
        self.title = form.getfirst('title', '', uni)
        self.locale = form.getfirst('locale', '', uni)
        self.rights = form.getlist('rights', uni)
        self.text = form.getfirst('text', '', uni)
    #enddef

    def save(self, req):
        source = req.cfg.pages_source + '/' + self.name
        with open (source + '.tmp', 'w+') as tmp:
            tmp.write(self.text.encode('utf-8'))
        if exists(source):      # backup old file
            backup = req.cfg.pages_history + '/' + self.name
            copyfile(source, backup + '.' + datetime.now().isoformat())
        rename(source + '.tmp', source)

        target = req.cfg.pages_out + '/' + self.name
        with open (target + '.tmp', 'w+') as tmp:
            tmp.write(generate_page(req,
                                "page.html", page = self).encode('utf-8'))
        rename(target + '.tmp', target)
    #enddef

    def check_right(self, req):
        """ check if any of login.rights metch any of page.rights """

        tran = req.db.transaction(req.logger)
        c = tran.cursor()
        c.execute("SELECT editor_rights FROM page WHERE page_id = %s", self.id)

        rights = json.loads(c.fetchone()[0])
        return match_right(req, rights)
    #enddef

    def check_filename(self):
        return True if re_filename.match(self.name) else False
    #enddef

    @staticmethod
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

            with open (req.cfg.pages_source + '/' + page.name, 'r') as f:
                page.text = f.read().decode('utf-8')

            target = req.cfg.pages_out + '/' + page.name
            with open (target + '.tmp', 'w+') as tmp:
                tmp.write(generate_page(req,
                                "page.html", page = page).encode('utf-8'))
            rename(target + '.tmp', target)
            row = c.fetchone()
        #endwhile
    #enddef

    @staticmethod
    def list(req, pager):
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
#endclass
