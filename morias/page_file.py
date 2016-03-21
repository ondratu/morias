# -*- coding: utf-8 -*-

from poorwsgi import app, state, redirect, SERVER_RETURN
from falias.sql import Sql

from morias.core.login import check_login, rights, check_right, \
    match_right, do_check_right, do_match_right, do_create_token, check_token
from morias.core.render import generate_page
from morias.core.errors import SUCCESS

from morias.lib.menu import Item
from morias.lib.pager import Pager
from morias.lib.page_file import Page
from morias.lib.rst import check_rst, rst2html
from morias.lib.timestamp import check_timestamp

from morias.admin import content_menu


_check_conf = (
    # morias common block
    ('morias', 'db', Sql),

    # pages block
    ('pages', 'source', str),
    ('pages', 'out', str, ''),
    ('pages', 'history', str, ''),
    ('pages', 'extra_rights', bool, False, True,
              "If pages have rights settings visible in editation."),
    ('pages', 'rights', tuple, '', True,
              "User rights, which could be use for page editing."),
    ('pages', 'index_is_root', bool, True),
    ('pages', 'runtime', bool, False),
    ('pages', 'runtime_without_html', bool, False),     # danger !
    ('pages', 'timestamp', unicode, 'tmp/pages.timestamp'),
)


def _call_conf(cfg, parser):
    def empty(req):
        return ()

    rights.update(cfg.pages_rights)
    if 'get_static_menu' not in cfg.__dict__:
        cfg.get_static_menu = empty             # set empty static menu
    if not cfg.pages_out:
        cfg.pages_runtime = True                # fallback for dynamic page
    if cfg.pages_index_is_root and not cfg.pages_runtime:
        app.set_route('/', root)                # redirect from / to index.html

    if cfg.pages_runtime:                       # auto register pages url
        refresh_page_files(cfg, cfg.pages_timestamp, False)

# enddef _call_conf

timestamp = -1

module_rights = ['pages_listall', 'pages_author', 'pages_modify']
rights.update(module_rights)

content_menu.append(Item('/admin/pages', label="Pages", symbol="files",
                    rights=module_rights))


@app.pre_process()
def corect_page_files(req):
    if req.uri_rule in ('_debug_info_', '_send_file_', '_directory_index_'):
        return  # this methods no need this pre process

    if req.cfg.pages_runtime:
        refresh_page_files(req, req.cfg.pages_timestamp)
# enddef


def refresh_page_files(req, cfg_timestamp, clear=True):
    global timestamp
    check = check_timestamp(req, cfg_timestamp)
    if check > timestamp:       # if last load was in past to timestamp file
        req.log_error("file timestamp is older, refresh page_files ...",
                      state.LOG_INFO)

        if clear:
            for uri, hdls in app.handlers.items():
                if hdls.get(state.METHOD_GET) == runtime_file:
                    app.pop_route(uri, state.METHOD_GET)
                    app.pop_route(uri, state.METHOD_HEAD)

        if req.cfg.pages_index_is_root:
            app.set_route('/', runtime_file)                # / will be index
        if req.cfg.pages_runtime_without_html:
            for it in Page.list(req.cfg, Pager(limit=-1)):
                name = it.name[:it.name.rfind('.')]
                if name in ('admin', 'user', 'login', 'logout'):
                    req.cfg.log_error('Denied runtime file uri: %s' %
                                      it.name[:-5], state.LOG_ERR)
                    continue
                req.cfg.log_info("Adding /%s" % name)
                app.set_route('/'+name, runtime_file)   # without .html
        else:
            for it in Page.list(req.cfg, Pager(limit=-1)):
                # rst not work
                app.set_route('/'+it.name, runtime_file)

        timestamp = check
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
        text = Page.text_by_name(req, req.uri[req.uri.rfind('/')+1:]+'.rst')
        if text is None:
            raise SERVER_RETURN(state.HTTP_NOT_FOUND)
        text = rst2html(text)

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
                                 page=page, rights=rights, error=error,
                                 extra_rights=req.cfg.pages_extra_rights)
    # endif
    if not page.get(req):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)
    return generate_page(req, "admin/pages_mod.html", token=token,
                         page=page, rights=rights,
                         extra_rights=req.cfg.pages_extra_rights)
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


@app.route('/admin/pages/rst', state.METHOD_POST)
def admin_pages_rst(req):
    check_login(req)
    match_right(req, module_rights)
    return check_rst(req)
