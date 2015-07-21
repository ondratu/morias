# -*- coding: utf-8 -*-

from poorwsgi import *
from falias.sql import Sql

import json

from core.login import rights, check_login, check_right, check_referer
from core.render import generate_page

from lib.pager import Pager
from lib.timestamp import check_timestamp
from lib.page_menu import MenuItem

from admin import *

_check_conf = (
    ('morias', 'db', Sql),                      # database configuration
    ('morias', 'static_menu', bool, True, True, "If static menu is append to menu"),
    ('page_menu', 'timestamp', unicode, 'tmp/page_menu.timestamp'),
)

def _call_conf(cfg, parser):
    cfg.get_static_menu = MenuItem.get_menu
    if cfg.morias_static_menu:
        refresh_menu(cfg, cfg.page_menu_timestamp)


timestamp = -1
static_menu = None

module_right = 'menu_modify'
rights.add(module_right)
content_menu.append(Item('/admin/menu', label="Menu", rights = [module_right]))

@app.pre_process()
def load_static_menu(req):
    if req.uri_rule in ('_debug_info_', '_send_file_', '_directory_index_'):
        return  # this methods no need this pre process

    if req.cfg.morias_static_menu:
        refresh_menu(req, req.cfg.page_menu_timestamp)
        req.static_menu.extend(static_menu)
#enddef

def refresh_menu(req, cfg_timestamp):
    """ refresh menu from db if timestamp is change """
    global timestamp
    global static_menu

    check = check_timestamp(req, cfg_timestamp)
    if check > timestamp:       # if last load was in past to timestamp file
        req.log_error("file timestamp is older, loading menu from DB...",
                        state.LOG_INFO)
        static_menu = MenuItem.get_menu(req)
        timestamp = check
#enddef

def js_items(req):
    pager = Pager(limit = -1)
    items = []
    for item in MenuItem.list(req, pager):
        items.append(item.__dict__)
    req.content_type = 'application/json'
    return json.dumps({'items': items})


@app.route('/admin/menu')
def admin_menu(req):
    check_login(req)
    check_right(req, module_right)

    pager = Pager(limit = -1)
    items = MenuItem.list(req, pager)

    return generate_page(req, "admin/page_menu.html",
                        pager = pager, items = items)
#enddef

@app.route('/admin/menu/<id:int>', method = state.METHOD_PUT)
@app.route('/admin/menu/add', method = state.METHOD_POST)
def admin_menu_add_update(req, id = None):
    check_login(req)
    check_right(req, module_right)
    check_referer(req, '/admin/menu')
    # TODO: check origin .... :/

    item = MenuItem(id)
    item.bind(req.form)
    if not item.title:
        req.status = state.HTTP_BAD_REQUEST
        req.content_type = 'application/json'
        return json.dumps({'reason': 'empty_title'})

    status = item.mod(req) if id else item.add(req)
    if status:
        return js_items(req)

    req.status = state.HTTP_BAD_REQUEST
    req.content_type = 'application/json'
    return json.dumps({'reason': 'title_exist'})
#enddef

@app.route('/admin/menu/<id:int>/delete', method = state.METHOD_DELETE)
def admin_menu_delete(req, id):
    check_login(req)
    check_right(req, module_right)
    check_referer(req, '/admin/menu')

    item = MenuItem(id)
    if item.delete(req):
        return js_items(req)

    req.status = state.HTTP_BAD_REQUEST
    req.content_type = 'application/json'
    return json.dumps({'reason': 'integrity_error'})
#enddef

@app.route('/admin/menu/<id:int>/move', method = state.METHOD_PUT)
def admin_menu_move(req, id):
    check_login(req)
    check_right(req, module_right)
    check_referer(req, '/admin/menu')

    item = MenuItem(id)
    item.bind(req.form)

    if item.move(req):
        return js_items(req)

    req.status = state.HTTP_BAD_REQUEST
    req.content_type = 'application/json'
    return json.dumps({'reason': 'integrity_error'})
#enddef

@app.route('/admin/menu/<id:int>/to_child', method = state.METHOD_PUT)
@app.route('/admin/menu/<id:int>/to_parent', method = state.METHOD_PUT)
def admin_menu_to(req, id):
    check_login(req)
    check_right(req, module_right)
    check_referer(req, '/admin/menu')

    item = MenuItem(id)

    status = item.to_child(req) if req.uri.endswith('to_child') else item.to_parent(req)
    if status:
        return js_items(req)

    req.status = state.HTTP_BAD_REQUEST
    req.content_type = 'application/json'
    return json.dumps({'reason': 'not_possible'})
#enddef
