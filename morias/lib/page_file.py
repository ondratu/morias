
import json, re

from os import rename, remove
from os.path import exists
from datetime import datetime
from shutil import copyfile

from falias.util import uni, nint

from core.render import generate_page
from core.login import match_right

#errors
EMPTY_FILENAME  = 1
BAD_FILENAME    = 2
PAGE_EXIST      = 3
PAGE_NOT_EXIST  = 4

re_filename = re.compile(r"^[\w\.-]+\.html$")

_drivers = ("sqlite",)

def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "page_file_" + req.db.driver
    return __import__("lib." + m).__getattribute__(m)
#enddef

class Page():
    def __init__(self, id = None):
        self.id = id

    def get(self, req):
        m = driver(req)
        m.get(self, req)

        with open (req.cfg.pages_source + '/' + self.name, 'r') as f:
            self.text = f.read().decode('utf-8')
    #enddef

    def add(self, req):
        if not self.name: return EMPTY_FILENAME

        if not self.check_filename(): return BAD_FILENAME

        m = driver(req)
        return m.add(self, req)
    #enddef

    def mod(self, req):
        if not self.name: return EMPTY_FILENAME

        if not self.check_filename(): return BAD_FILENAME

        m = driver(req)
        return m.mod(self, req)
    #enddef

    def delete(self, req):
        m = driver(req)
        return m.delete(self, req)

    def bind(self, form):
        self.id = form.getfirst('page_id', self.id, nint)
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

    def remove(self, req, rights):
        # meta file about deleted page
        backup = req.cfg.pages_history + '/' + self.name
        with open (backup + '.' + datetime.now().isoformat() + '.deleted' , 'w+') as tmp:
            tmp.write("title: %s\n" % self.title.encode('utf-8'))
            tmp.write("locale: %s\n" % self.locale)
            tmp.write("editor_rights: %s\n" % rights)

        source = req.cfg.pages_source + '/' + self.name
        if exists(source):      # backup old file
            backup = req.cfg.pages_history + '/' + self.name
            rename(source, backup + '.' + datetime.now().isoformat())

        target = req.cfg.pages_out + '/' + self.name
        if exists(target):      # delete output file
            remove(target)
    #enddef

    def regenerate(self, req):
        with open (req.cfg.pages_source + '/' + self.name, 'r') as f:
            self.text = f.read().decode('utf-8')

        target = req.cfg.pages_out + '/' + self.name
        with open (target + '.tmp', 'w+') as tmp:
            tmp.write(generate_page(req,
                                "page.html", page = self).encode('utf-8'))
        rename(target + '.tmp', target)
    #enddef


    def check_right(self, req):
        """ check if any of login.rights metch any of page.rights """
        m = driver(req)
        return match_right(req, m.load_rights(self, req))
    #enddef

    def check_filename(self):
        return True if re_filename.match(self.name) else False

    @staticmethod
    def regenerate_all(req):
        m = driver(req)
        m.regenerate_all(req)

    @staticmethod
    def list(req, pager):
        m = driver(req)
        return m.item_list(req, pager)

#endclass
