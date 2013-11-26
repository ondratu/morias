# -*- coding: utf-8 -*-

from poorwsgi import *
from falias.sql import Sql

import core.login

from admin import *

from core.render import generate_page

from lib.menu import Item
from lib.pager import Pager
from lib.page_file import Page

_check_conf = (
    # morias common block
    ('morias', 'db', Sql, None),

    # pages block
    ('pages', 'source', str,  None),
    ('pages', 'out',   str,  None),
)

core.login.rights += ['text_create', 'text_edit', 'text_delete']

admin_menu.append(Item('/admin/page', label="Pages"))

@app.route("/page/test/db")
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

@app.route('/')
def root(req):
    redirect(req, '/index.html', text="static index");

@app.route('/admin/page')
def admin_page(req):
    check_login(req, '/login?referer=/admin/page')
    check_right(req, 'admin')

    form = FieldStorage(req)

    pager = Pager()
    pager.bind(form)

    rows = Page.list(req, pager)
    return generate_page(req, "admin/page.html", menu = admin_menu,
                         pager = pager, rows = rows)
#enddef

@app.route('/admin/page/add', method = state.METHOD_GET_POST)
def admin_page_add(req):
    check_login(req, '/login?referer=/admin/page/add')
    check_right(req, 'admin')

    if req.method = 'POST':
        form = FieldStorage(req)
        page = Page()
        page.bind(req)
        error = page.add(req)

        if error:
            return generate_page(req, "admin/page_add.html", menu = admin_menu,
                         page = page, error = error)

        redirect(req, '/admin/page/mod?page_id=%d' % page.id)
    #end

    return generate_page(req, "admin/page_add.html", menu = admin_menu)
#enddef

@app.route('/admin/page/mod', state.METHOD_GET_POST)
def admin_page_mod(req):
    check_login(req, '/login?referer=/admin/page/add')
    check_right(req, 'admin')

    form = FieldStorage(req)
    page = Page(form.getfirst('page_id', 0, int))
    if req.method = 'POST':
        page.bind(req)
        error = page.mod(req)

        if error:
            return generate_page(req, "admin/page_mod.html", menu = admin_menu,
                         page = page, error = error)
    #end
    page.get(req)
    return generate_page(req, "admin/page_mod.html", menu = admin_menu,
                         page = page)
