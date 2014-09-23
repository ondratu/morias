# -*- coding: utf-8 -*-

from poorwsgi import *

import json

from core.login import rights, check_login, check_right
from core.render import generate_page

from lib.pager import Pager
from lib.page_menu import MenuItem

from admin import *

def _call_conf(cfg, parser):
    cfg.get_static_menu = MenuItem.get_menu

module_right = 'menu_modify'
rights.add(module_right)

content_menu.append(Item('/admin/menu', label="Menu", rights = [module_right]))

@app.route('/admin/menu')
def admin_menu(req):
    check_login(req)
    check_right(req, module_right)

    pager = Pager(limit = -1)
    items = MenuItem.list(req, pager)

    return generate_page(req, "admin/page_menu.html",
                        pager = pager, items = items)
#enddef

@app.route('/admin/menu/<id:int>', method = state.METHOD_POST)
@app.route('/admin/menu/add', method = state.METHOD_POST)
def admin_menu_add_update(req, id = None):
    check_login(req)
    check_right(req, module_right)

    item = MenuItem(id)
    item.bind(req.form)
    if not item.title:
        req.status = state.HTTP_BAD_REQUEST
        req.content_type = 'application/json'
        return json.dumps({'reason': 'empty_title'})

    status = item.mod(req) if id else item.add(req)
    if status:
        pager = Pager(limit = -1)
        items = []
        for item in MenuItem.list(req, pager):
            items.append(item.__dict__)
        req.content_type = 'application/json'
        return json.dumps({'items': items})

    req.status = state.HTTP_BAD_REQUEST
    req.content_type = 'application/json'
    return json.dumps({'reason': 'title_exist'})
#enddef

@app.route('/admin/menu/<id:int>/delete', method = state.METHOD_POST)
def admin_menu_delete(req, id):
    check_login(req)
    check_right(req, module_right)

    item = MenuItem(id)
    if item.delete(req):
        pager = Pager(limit = -1)
        items = []
        for item in MenuItem.list(req, pager):
            items.append(item.__dict__)
        req.content_type = 'application/json'
        return json.dumps({'items': items})

    req.status = state.HTTP_BAD_REQUEST
    req.content_type = 'application/json'
    return json.dumps({'reason': 'integrity_error'})
#enddef
