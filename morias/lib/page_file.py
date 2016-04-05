from falias.util import uni, nint
from poorwsgi import state

from os import rename, remove, access, R_OK, W_OK
from os.path import exists, isdir, getmtime
from datetime import datetime
from shutil import copyfile

import re
import json

from morias.core.render import generate_page
from morias.core.login import do_match_right, do_check_right

from morias.lib.rst import rst2html
from morias.lib.timestamp import write_timestamp

# errors
EMPTY_FILENAME = 1
BAD_FILENAME = 2
PAGE_EXIST = 3
PAGE_NOT_EXIST = 4

FORMAT_HTML = 1
FORMAT_RST = 2

re_filename = re.compile(r"^[\w\.-]+\.(html|rst)$")

_drivers = ("sqlite",)


def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "page_file_" + req.db.driver
    return __import__("morias.lib." + m).lib.__getattribute__(m)


class Page():
    def __init__(self, id=None):
        self.id = id

    def from_row(self, row):
        for key in row.keys():
            val = row[key]
            if key == 'page_id':
                self.id = val
            elif key == 'rights':
                self.rights = json.loads(val)
            else:
                setattr(self, key, val)
    # enddef

    def get_modify(self, req):
        page_file_name = req.cfg.pages_source + '/' + self.name
        if exists(page_file_name):
            self.modify = datetime.fromtimestamp(getmtime(page_file_name))
            self.found = True
        else:
            self.found = False

    def get(self, req):
        m = driver(req)
        if m.get(self, req):
            with open(req.cfg.pages_source + '/' + self.name, 'r') as f:
                self.text = f.read().decode('utf-8')
            return self
        return None
    # enddef

    @staticmethod
    def text_by_name(req, name):
        try:
            with open(req.cfg.pages_source + '/' + name, 'r') as f:
                return f.read().decode('utf-8')
        except IOError as e:
            req.log_error(str(e), state.LOG_INFO)
            return None
    # enddef

    def add(self, req):
        if not self.name:
            return EMPTY_FILENAME
        if not self.check_filename():
            return BAD_FILENAME

        m = driver(req)
        rv = m.add(self, req)
        write_timestamp(req, req.cfg.pages_timestamp)
        return rv
    # enddef

    def mod(self, req):
        if not self.name:
            return EMPTY_FILENAME
        if not self.check_filename():
            return BAD_FILENAME

        m = driver(req)
        rv = m.mod(self, req)
        write_timestamp(req, req.cfg.pages_timestamp)
        return rv
    # enddef

    def delete(self, req):
        m = driver(req)
        rv = m.delete(self, req)
        write_timestamp(req, req.cfg.pages_timestamp)
        return rv

    def bind(self, form, author_id=None):
        self.id = form.getfirst('page_id', self.id, nint)
        for attr in ('name', 'title', 'locale', 'text'):
            setattr(self, attr, form.getfirst(attr, '', uni))
        self.rights = form.getlist('rights', uni)
        self.format = form.getfirst('format', FORMAT_HTML, int)
        if author_id:
            self.author_id = author_id
    # enddef

    def save(self, req):
        source = req.cfg.pages_source + '/' + self.name
        with open(source + '.tmp', 'w+') as tmp:
            tmp.write(self.text.encode('utf-8'))
        if exists(source):      # backup old file
            backup = req.cfg.pages_history + '/' + self.name
            copyfile(source, backup + '.' + datetime.now().isoformat())
        rename(source + '.tmp', source)

        if req.cfg.pages_runtime:
            return              # not need when paeges are runtime generated

        target = req.cfg.pages_out + '/' + self.name
        if self.format == FORMAT_RST:
            self.html = rst2html(self.text)
            target += '.html'

        with open(target + '.tmp', 'w+') as tmp:
            tmp.write(generate_page(
                req, "page_file.html", page=self,
                staticmenu=req.cfg.get_static_menu(req)).encode('utf-8'))
        rename(target + '.tmp', target)
    # enddef

    def remove(self, req):
        # meta file about deleted page
        backup = req.cfg.pages_history + '/' + self.name
        b_name = backup + '.' + datetime.now().isoformat() + '.deleted'
        with open(b_name, 'w+') as tmp:
            tmp.write("title: %s\n" % self.title.encode('utf-8'))
            tmp.write("author_id: %ds\n" % self.author_id)
            tmp.write("locale: %s\n" % self.locale)
            tmp.write("format: %s\n" % self.format)
            tmp.write("editor_rights: %s\n" % json.dumps(self.rights))

        source = req.cfg.pages_source + '/' + self.name
        if exists(source):      # backup old file
            rename(source, backup + '.' + datetime.now().isoformat())

        target = req.cfg.pages_out + '/' + self.name
        if req.cfg.pages_out and exists(target):    # delete output file
            remove(target)
    # enddef

    def regenerate(self, req):
        if req.cfg.pages_runtime:
            return              # not need where runtime is True
        with open(req.cfg.pages_source + '/' + self.name, 'r') as f:
            self.text = f.read().decode('utf-8')

        target = req.cfg.pages_out + '/' + self.name
        if self.format == FORMAT_RST:
            self.html = rst2html(self.text)
            target += '.html'

        with open(target + '.tmp', 'w+') as tmp:
            tmp.write(generate_page(
                req, "page_file.html", page=self,
                staticmenu=req.cfg.get_static_menu(req)).encode('utf-8'))
        rename(target + '.tmp', target)
    # enddef

    def check_right(self, req):
        """ check if any of login.rights metch any of page.rights """
        m = driver(req)
        m.load_rights(self, req)
        if do_match_right(req, 'pages_modify'):
            return True     # user is editor
        elif do_check_right(req, 'pages_author') \
                and self.author_id == req.login.id:
            return True     # user is author
        elif self.rights and do_match_right(req, self.rights):
            return True     # user has special right which have page
        return False
    # enddef

    def check_filename(self):
        return True if re_filename.match(self.name) else False

    @staticmethod
    def regenerate_all(req):
        m = driver(req)
        m.regenerate_all(req)

    @staticmethod
    def list(req, pager, **kwargs):
        if pager.order not in ('name', 'title', 'locale'):
            pager.order = 'name'

        m = driver(req)
        return m.item_list(req, pager, **kwargs)

    @staticmethod
    def test(req):
        m = driver(req)
        return m.test(req)

    @staticmethod
    def test_dirs(req):

        def read_access(d):
            return access(d, R_OK)

        def write_access(d):
            return access(d, W_OK)

        dirs = [req.cfg.pages_source]
        if not req.pages_runtime:
            dirs.append(req.cfg.pages_out)
        if req.cfg.pages_history:
            dirs.append(req.cfg.pages_history)

        for d in dirs:
            for fn in (exists, isdir, read_access, write_access):
                assert fn(d)
# endclass
