# This module is simple eshop-store, so you can create items, appended to store,
# or removing from store

from poorwsgi import *
from falias.sql import Sql

import json

from core.login import rights, check_login, check_right, check_referer
from core.render import generate_page

from lib.menu import Item as MenuItem
from lib.pager import Pager
from lib.eshop_store import Item, Action, \
        STATE_VISIBLE, STATE_HIDDEN, STATE_DISABLED, ACTION_INC, ACTION_DEC, ACTION_PRI

from eshop import eshop_menu

_check_conf = (
    # morias common block
    ('morias', 'db', Sql, None),
)

module_right = 'eshop_store'
rights.add(module_right)

eshop_menu.append(MenuItem('/admin/eshop/store', label="Store",
                         rights = [module_right]))


@app.route('/admin/eshop/store')
def admin_menu(req):
    check_login(req)
    check_right(req, module_right)

    show = req.args.getfirst('show', '', uni)
    if show == 'visible':
        kwargs = {'state': STATE_VISIBLE}
    elif show == 'hidden':
        kwargs = {'state': STATE_HIDDEN}
    elif show == 'disabled':
        kwargs = {'state': STATE_DISABLED}
    else:
        kwargs = {}

    pager = Pager()
    items = Item.list(req, pager, **kwargs)

    return generate_page(req, "admin/eshop/store.html",
                        pager = pager, items = items, show = show)
#enddef

@app.route('/admin/eshop/store/<id:int>/actions')
def admin_item_actions(req, item_id):
    check_login(req)
    check_right(req, module_right)
    check_referer(req, '/admin/eshop/store/%s' % item_id)

    action_type = req.args.getfirst('type', '', uni)
    if action_type == 'inc':
        kwargs = {'action_type': ACTION_INC}
    elif action_type == 'dec':
        kwargs = {'action_type': ACTION_DEC}
    elif action_type == 'pri':
        kwargs = {'action_type': ACTION_PRI}
    else:
        kwargs = {}
    kwargs['item_id'] = item_id

    pager = Pager(sort = 'desc')
    pager.bind(req.args)

    actions = list(a.__dict__ for a in Action.list(req, pager, **kwargs))
    req.content_type = 'application/json'
    return json.dumps({'actions': actions, 'pager': pager.__dict__})
#enddef

@app.route('/admin/eshop/store/add', method = state.METHOD_GET_POST)
def admin_item_add(req):
    check_login(req)
    check_right(req, module_right)

    item = Item()
    if req.method == 'POST':
        item.bind(req.form)
        error = item.add(req)

        if error != item:
            return generate_page(req, "admin/eshop/item_mod.html",
                        item = item, error = error)

        redirect(req, '/admin/eshop/store/%d' % item.id)
    #end

    return generate_page(req, "admin/eshop/item_mod.html", item = item)
#enddef

@app.route('/admin/eshop/store/<id:int>', state.METHOD_GET_POST)
def admin_item_mod(req, id):
    check_login(req)
    check_right(req, module_right)

    item = Item(id)
    if req.method == 'POST':
        item.bind(req.form)
        error = item.mod(req)
        if error != item:
            return generate_page(req, "admin/eshop/item_mod.html",
                        item = item, error = error)

    if not item.get(req):    # still fresh data
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    return generate_page(req, "admin/eshop/item_mod.html", item = item)
#enddef

@app.route('/admin/eshop/store/<id:int>/disable', state.METHOD_POST)
@app.route('/admin/eshop/store/<id:int>/hidden', state.METHOD_POST)
@app.route('/admin/eshop/store/<id:int>/visible', state.METHOD_POST)
def admin_item_state(req, id):
    check_login(req, '/login?referer=/admin/eshop/store')
    check_right(req, module_right)
    check_referer(req, '/admin/eshop/store')

    item = Item(id)
    if not item.get(req):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    if req.uri.endswith('/visible'):
        item.set_state(req, STATE_VISIBLE)
    elif req.uri.endswith('/hidden'):
        item.set_state(req, STATE_HIDDEN)
    else:
        item.set_state(req, STATE_DISABLED)

    redirect(req, '/admin/eshop/store')
#enddef

#@app.route('/admin/eshop/store/<id:int>/dec', method = state.METHOD_POST)
@app.route('/admin/eshop/store/<id:int>/inc', method = state.METHOD_POST)
@app.route('/admin/eshop/store/<id:int>/pri', method = state.METHOD_POST)
def admin_item_incdec(req, id):
    check_login(req, '/login?referer=/admin/eshop/store/%s' % id)
    check_right(req, module_right)
    check_referer(req, '/admin/eshop/store/%s' % id)

    if req.uri.endswith('/inc'):
        action_type = ACTION_INC
    elif req.uri.endswith('/dec'):
        action_type = ACTION_DEC
    elif req.uri.endswith('/pri'):
        action_type = ACTION_PRI
    else:
        raise RuntimeError('Unknow action')

    action = Action()
    action.bind(req.form, action_type)

    item = Item(id)
    if not item.action(req, action) or not item.get(req):
        req.status = state.HTTP_NOT_FOUND
        req.content_type = 'application/json'
        return json.dumps({'reason': 'item not found'})

    req.content_type = 'application/json'
    return json.dumps({'item': item.__dict__})
#enddef
