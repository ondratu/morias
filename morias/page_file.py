# -*- coding: utf-8 -*-

from poorwsgi import *
from falias.sql import Sql

from os.path import exists, isdir
from os import access, R_OK, W_OK

from core.login import check_login, rights, check_referer, check_right, \
                    match_right, do_check_right
from core.render import generate_page
from core.errors import SUCCESS

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
    ('pages', 'rights', tuple, '')
)

def _call_conf(cfg, parser):
    def empty(req):
        return ()

    rights.update(cfg.pages_rights)
    if 'get_static_menu' not in cfg.__dict__: cfg.get_static_menu = empty
#enddef

module_rights = ['pages_listall', 'pages_author', 'pages_modify']
rights.update(module_rights)

content_menu.append(Item('/admin/pages', label="Pages", symbol="files",
                    rights = module_rights))

@app.route("/test/pages/db")
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

@app.route("/test/pages/dirs")
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

@app.route('/admin/pages')
def admin_pages(req):
    check_login(req)
    match_right(req, module_rights)

    error = req.args.getfirst('error', 0, int)

    pager = Pager()
    pager.bind(req.args)

    if not do_match_right(req, ('pages_modify', 'pages_listall')):
        rows = Page.list(req, pager, author_id = req.login.id)
    else:
        rows = Page.list(req, pager)
    return generate_page(req, "admin/pages.html",
                        pager = pager, rows = rows, error = error)
#enddef

@app.route('/admin/pages/add', method = state.METHOD_GET_POST)
def admin_pagse_add(req):
    check_login(req)
    match_right(req, ('pages_author', 'pages_modify'))

    if req.method == 'POST':
        page = Page()
        page.bind(req.form, req.login.id)
        error = page.add(req)

        if error:
            return generate_page(req, "admin/pages_mod.html",
                        rights = rights,
                        page = page, error = error)

        redirect(req, '/admin/pages/%d' % page.id)
    #end

    return generate_page(req, "admin/pages_mod.html",
                        rights = rights)
#enddef

@app.route('/admin/pages/<id:int>', state.METHOD_GET_POST)
def admin_pages_mod(req, id):
    """ Edit page could:
            * author of page, if still have pages_author right
            * admin with pages_modify right
            * admin with pages_listall right and right which must have page too
    """
    check_login(req)
    match_right(req, module_rights)

    page = Page(id)
    if (not do_check_right(req, 'pages_modify')) and (not page.check_right(req)):
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)

    if req.method == 'POST':
        page.bind(req.form)
        error = page.mod(req)
        if error:
            return generate_page(req, "admin/pages_mod.html",
                                    page = page,
                                    rights = rights,
                                    error = error)
        #endif
    #end
    if not page.get(req):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)
    return generate_page(req, "admin/pages_mod.html",
                        rights = rights,
                        page = page)
#enddef

@app.route('/admin/pages/<id:int>/delete', state.METHOD_POST)
def admin_pages_del(req, id):
    """ Delete page, could:
            * author of page if have still pages_author right
            * admin with pages_modify
    """

    check_login(req, '/login?referer=/admin/pages')
    match_right(req, ('pages_author', 'pages_modify'))
    check_referer(req, '/admin/pages')

    page = Page(id)
    if not page.check_right(req):
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)

    page.delete(req)
    # TODO: redirect to same page
    redirect(req, '/admin/pages?error=%d' % SUCCESS)
#enddef

@app.route('/admin/pages/all/regenerate', state.METHOD_POST)
def admin_pages_regenerate_all(req):
    check_login(req, '/login?referer=/admin/pages')
    check_right(req, 'pages_modify')

    Page.regenerate_all(req)

    # TODO: redirect to same page
    redirect(req, '/admin/pages?error=%d' % SUCCESS)
#enddef
