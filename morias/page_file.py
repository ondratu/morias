# -*- coding: utf-8 -*-

from poorwsgi import *
from falias.sql import Sql

from os.path import exists, isdir
from os import access, R_OK, W_OK

from core.login import check_login, rights, check_referer
from core.render import generate_page
from core.errors import ACCESS_DENIED, SUCCESS

from lib.menu import Item
from lib.pager import Pager
from lib.page_file import Page

from admin import *

_check_conf = (
    # morias common block
    ('morias', 'db', Sql, None),

    # pages block
    ('pages', 'source', str, None),
    ('pages', 'out', str, None),
    ('pages', 'history', str, ''),
)

rights += ['page_list', 'page_create', 'page_edit', 'page_delete']

admin_menu.append(Item('/admin/page', label="Pages", rights = ['page_list']))

@app.route("/test/page/db")
def test_db(req):
    data = (None, 123, 3.14, "úspěšný test", "'; SELECT 1; SELECT")
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT %s, %s, %s, %s, %s", data)
    copy = tuple(it.encode('utf-8') if isinstance(it, unicode) else it \
                        for it in c.fetchone())
    tran.commit()

    req.content_type = "text/plain; charset=utf-8"
    if copy == data:
        return "Test Ok\n" + str(data) + '\n' + str(copy)
    else:
        return "Test failed\n" + str(data) + '\n' + str(copy)
#enddef

@app.route("/test/page/dirs")
def test_dirs(req):
    retval = ""
    error = False

    def read_access(d):
        return access(d, R_OK)

    def write_access(d):
        return access(d, W_OK)

    dirs = [req.cfg.pages_source, req.cfg.pages_out]
    if req.cfg.pages_history: dirs.append(req.cfg.pages_history)

    for d in dirs:
        for fn in (exists, isdir, read_access, write_access):
            tmp = fn(d)
            line = "Dir %s %s" % (d, fn.__name__)
            retval += "%s %s %s\n" % (line, "." * (70 - len(line)), tmp)
            error = not tmp or error
    retval += "\nTest" + " " * 68 + ("Failed" if error else "Pass")

    req.content_type = "text/plain; charset=utf-8"
    return retval
#enddef

@app.route('/')
def root(req):
    redirect(req, '/index.html', text="static index");

@app.route('/admin/page')
def admin_page(req):
    check_login(req, '/login?referer=/admin/page')
    check_right(req, 'page_list')

    error = req.args.getfirst('error', 0, int)

    pager = Pager()
    pager.bind(req.args)

    rows = Page.list(req, pager)
    return generate_page(req, "admin/page.html",
                        menu = correct_menu(req, admin_menu),
                        pager = pager, rows = rows, error = error)
#enddef

@app.route('/admin/page/add', method = state.METHOD_GET_POST)
def admin_page_add(req):
    check_login(req, '/login?referer=/admin/page/add')
    check_right(req, 'page_create', '/admin/page?error=%d' % ACCESS_DENIED)

    if req.method == 'POST':
        page = Page()
        page.bind(req.form)
        error = page.add(req)

        if error:
            return generate_page(req, "admin/page_mod.html",
                        menu = correct_menu(req, admin_menu),
                        rights = rights,
                        page = page, error = error)

        redirect(req, '/admin/page/mod?page_id=%d' % page.id)
    #end

    return generate_page(req, "admin/page_mod.html",
                        menu = correct_menu(req, admin_menu),
                        rights = rights)
#enddef

@app.route('/admin/page/mod', state.METHOD_GET_POST)
def admin_page_mod(req):
    check_login(req, '/login?referer=/admin/page/mod')
    check_right(req, 'page_edit', '/admin/page?error=%d' % ACCESS_DENIED)

    page = Page(req.args.getfirst('page_id', 0, int))
    if not page.check_right(req):
        redirect(req, '/admin/page?error=%d' % ACCESS_DENIED)

    if req.method == 'POST':
        page.bind(req.form)
        error = page.mod(req)
        if error:
            return generate_page(req, "admin/page_mod.html",
                                    menu = correct_menu(req, admin_menu),
                                    page = page,
                                    rights = rights,
                                    error = error)
        #endif
    #end
    page.get(req)
    return generate_page(req, "admin/page_mod.html",
                        menu = correct_menu(req, admin_menu),
                        rights = rights,
                        page = page)
#enddef

@app.route('/admin/page/del', state.METHOD_POST)
def admin_page_del(req):
    check_login(req, '/login?referer=/admin/page/mod')
    check_right(req, 'page_delete', '/admin/page?error=%d' % ACCESS_DENIED)
    check_referer(req, '/admin/page')

    page = Page(req.form.getfirst('page_id', 0, int))
    if not page.check_right(req):
        redirect(req, '/admin/page?error=%d' % ACCESS_DENIED)

    page.delete(req)
    redirect(req, '/admin/page?error=%d' % SUCCESS)
#enddef

@app.route('/admin/page/regenerate/all')
def admin_page_regenerate_all(req):
    check_login(req, '/login?referer=/admin/page/regenerate')
    check_right(req, 'super', '/admin/page?error=%d' % ACCESS_DENIED)

    Page.regenerate_all(req)

    redirect(req, '/admin/page?error=%d' % SUCCESS)
#enddef
