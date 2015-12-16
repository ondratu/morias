# -*- coding: utf-8 -*-

from poorwsgi import app, state, redirect, SERVER_RETURN
from falias.sql import Sql

from os.path import exists, isdir
from os import access, R_OK, W_OK

from core.login import check_login, rights, check_right, \
    match_right, do_check_right, do_match_right, do_create_token, check_token
from core.render import generate_page
from core.errors import SUCCESS

from lib.menu import Item
from lib.pager import Pager
from lib.page_file import Page

from admin import content_menu


_check_conf = (
    # morias common block
    ('morias', 'db', Sql),

    # pages block
    ('pages', 'source', str),
    ('pages', 'out', str, ''),
    ('pages', 'history', str, ''),
    ('pages', 'rights', tuple, '', True,
              "User rights, which could be use for page editing."),
    ('pages', 'redirect_to_index', bool, True),
    ('pages', 'runtime', bool, False),
    ('pages', 'runtime_without_html', bool, False)      # danger !
)


def _call_conf(cfg, parser):
    def empty(req):
        return ()

    rights.update(cfg.pages_rights)
    if 'get_static_menu' not in cfg.__dict__:
        cfg.get_static_menu = empty             # set empty static menu
    if not cfg.pages_out:
        cfg.pages_runtime = True                # fallback for dynamic page
    if cfg.pages_redirect_to_index and not cfg.pages_runtime:
        app.set_route('/', root)                # redirect from / to index.html

    if cfg.pages_runtime:                    # auto register pages url
        if cfg.pages_redirect_to_index:
            app.set_route('/', runtime_file)                # / will be index
        if cfg.pages_runtime_without_html:
            for it in Page.list(cfg, Pager()):
                if it.name[:-5] in ('admin', 'user', 'login', 'logout'):
                    cfg.log_error('Denied runtime file uri: %s' % it.name[:-5],
                                  state.LOG_ERR)
                    continue
                app.set_route('/'+it.name[:-5], runtime_file)   # without .html
        else:
            for it in Page.list(cfg, Pager()):
                app.set_route('/'+it.name, runtime_file)
# enddef _call_conf

module_rights = ['pages_listall', 'pages_author', 'pages_modify']
rights.update(module_rights)

content_menu.append(Item('/admin/pages', label="Pages", symbol="files",
                    rights=module_rights))


@app.route("/test/pages/db")
def test_db(req):
    data = (None, 123, 3.14, "úspěšný test", "'; SELECT 1; SELECT")
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT %s, %s, %s, %s, %s", data)
    copy = tuple(it.encode('utf-8') if isinstance(it, unicode) else it
                 for it in c.fetchone())
    tran.commit()

    req.content_type = "text/plain; charset=utf-8"
    if copy == data:
        return "Test Ok\n" + str(data) + '\n' + str(copy)
    else:
        return "Test failed\n" + str(data) + '\n' + str(copy)
# enddef


@app.route("/test/pages/dirs")
def test_dirs(req):
    retval = ""
    error = False

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
            tmp = fn(d)
            line = "Dir %s %s" % (d, fn.__name__)
            retval += "%s %s %s\n" % (line, "." * (70 - len(line)), tmp)
            error = not tmp or error
    retval += "\nTest" + " " * 68 + ("Failed" if error else "Pass")

    req.content_type = "text/plain; charset=utf-8"
    return retval
# enddef


def root(req):
    redirect(req, '/index.html', text="static index")


def runtime_file(req):
    text = None
    if req.uri == '/':
        text = Page.text_by_name(req, 'index.html')
    elif req.uri.endswith('.html'):
        text = Page.text_by_name(req, req.uri[req.uri.rfind('/')+1:])
    else:       # without .html
        text = Page.text_by_name(req, req.uri[req.uri.rfind('/')+1:]+'.html')

    if text is None:
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    return generate_page(req, 'runtime_file.html', text=text, runtime=True)
# enddef


@app.route('/admin/pages')
def admin_pages(req):
    check_login(req)
    match_right(req, module_rights)

    error = req.args.getfirst('error', 0, int)

    pager = Pager()
    pager.bind(req.args)

    if not do_match_right(req, ('pages_modify', 'pages_listall')):
        rows = Page.list(req, pager, author_id=req.login.id)
    else:
        rows = Page.list(req, pager)
    return generate_page(req, "admin/pages.html",
                         token=do_create_token(req, '/admin/pages'),
                         pager=pager, rows=rows, error=error)
# enddef


@app.route('/admin/pages/add', method=state.METHOD_GET_POST)
def admin_pagse_add(req):
    check_login(req)
    match_right(req, ('pages_author', 'pages_modify'))
    token = do_create_token(req, '/admin/pages/add')

    if req.method == 'POST':
        check_token(req, req.form.get('token'))
        page = Page()
        page.bind(req.form, req.login.id)
        error = page.add(req)

        if error:
            return generate_page(req, "admin/pages_mod.html", token=token,
                                 rights=rights, page=page, error=error)

        redirect(req, '/admin/pages/%d' % page.id)
    # end

    return generate_page(req, "admin/pages_mod.html", token=token,
                         rights=rights)
# enddef


@app.route('/admin/pages/<id:int>', state.METHOD_GET_POST)
def admin_pages_mod(req, id):
    """Edit page could:

    * author of page, if still have pages_author right
    * admin with pages_modify right
    * admin with pages_listall right and right which must have page too
    """
    check_login(req)
    match_right(req, module_rights)
    token = do_create_token(req, '/admin/pages/%d' % id)

    page = Page(id)
    if (not do_check_right(req, 'pages_modify')) \
            and (not page.check_right(req)):
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)

    if req.method == 'POST':
        check_token(req, req.form.get('token'))
        page.bind(req.form)
        error = page.mod(req)
        if error:
            return generate_page(req, "admin/pages_mod.html", token=token,
                                 page=page, rights=rights, error=error)
    # endif
    if not page.get(req):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)
    return generate_page(req, "admin/pages_mod.html", token=token,
                         page=page, rights=rights)
# enddef


@app.route('/admin/pages/<id:int>/delete', state.METHOD_POST)
def admin_pages_del(req, id):
    """ Delete page, could:
            * author of page if have still pages_author right
            * admin with pages_modify
    """

    check_login(req, '/log_in?referer=/admin/pages')
    match_right(req, ('pages_author', 'pages_modify'))
    check_token(req, req.form.get('token'))

    page = Page(id)
    if not page.check_right(req):
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)

    page.delete(req)
    # TODO: redirect to same page
    redirect(req, '/admin/pages?error=%d' % SUCCESS)
# enddef


@app.route('/admin/pages/all/regenerate', state.METHOD_POST)
def admin_pages_regenerate_all(req):
    check_login(req, '/log_in?referer=/admin/pages')
    check_right(req, 'pages_modify')

    Page.regenerate_all(req)

    # TODO: redirect to same page
    redirect(req, '/admin/pages?error=%d' % SUCCESS)
# enddef
