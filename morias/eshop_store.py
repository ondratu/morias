"""
This module is simple eshop-store, so you can create items, appended to store,
or removing from store
"""
from poorwsgi import app, state, redirect, SERVER_RETURN, uni
from falias.sql import Sql

import json

from core.login import rights, check_login, check_right, check_referer, \
    create_token, do_check_mgc
from core.render import generate_page

from lib.menu import Item as MenuItem
from lib.pager import Pager
from lib.eshop_store import Item, Action, \
    STATE_VISIBLE, STATE_HIDDEN, STATE_DISABLED, ACTION_INC, ACTION_DEC, \
    ACTION_PRI
from lib.attachments import Attachment

from user import user_sections
from eshop import eshop_menu

_check_conf = (
    # morias common block
    ('morias', 'db', Sql, None),
    # eshop block
    ('eshop', 'currency', unicode, '', True),
    ('eshop', 'eshop_in_menu',  bool, True),
)


def _call_conf(cfg, parser):
    if cfg.eshop_eshop_in_menu:
        user_sections.append(MenuItem('/eshop', label="Eshop"))

module_right = 'eshop_store'
rights.add(module_right)

eshop_menu.append(MenuItem('/admin/eshop/store', label="Store",
                           symbol="eshop-store", rights=[module_right]))


@app.route('/admin/eshop/store')
def admin_store(req):
    check_login(req)
    check_right(req, module_right)

    pager = Pager(sort='desc')
    pager.bind(req.args)

    show = req.args.getfirst('show', '', uni)
    if show == 'visible':
        kwargs = {'state': STATE_VISIBLE}
        pager.set_params(show=show)
    elif show == 'hidden':
        kwargs = {'state': STATE_HIDDEN}
        pager.set_params(show=show)
    elif show == 'disabled':
        kwargs = {'state': STATE_DISABLED}
        pager.set_params(show=show)
    else:
        kwargs = {}

    items = Item.list(req, pager, **kwargs)

    return generate_page(req, "admin/eshop/store.html",
                         pager=pager, items=items, show=show)
# enddef /admin/eshop/store


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

    pager = Pager(sort='desc')
    pager.bind(req.args)

    actions = list(a.__dict__ for a in Action.list(req, pager, **kwargs))
    req.content_type = 'application/json'
    return json.dumps({'actions': actions, 'pager': pager.__dict__})
# enddef /admin/eshop/store/<id:int>/actions


@app.route('/admin/eshop/store/add', method=state.METHOD_GET_POST)
def admin_item_add(req):
    check_login(req)
    check_right(req, module_right)

    item = Item()
    if req.method == 'POST':
        item.bind(req.form)
        error = item.add(req)

        if error != item:
            return generate_page(req, "admin/eshop/item_mod.html",
                                 item=item, error=error)

        redirect(req, '/admin/eshop/store/%d' % item.id)
    # endif

    return generate_page(req, "admin/eshop/item_mod.html", item=item)
# enddef


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
                                 item=item, error=error)

    if not item.get(req):    # still fresh data
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    return generate_page(req, "admin/eshop/item_mod.html", item=item)
# enddef


@app.route('/admin/eshop/store/<id:int>/disable', state.METHOD_POST)
@app.route('/admin/eshop/store/<id:int>/hidden', state.METHOD_POST)
@app.route('/admin/eshop/store/<id:int>/visible', state.METHOD_POST)
def admin_item_state(req, id):
    check_login(req, '/log_in?referer=/admin/eshop/store')
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

    redirect(req, req.referer)
# enddef


# TODO: /admin/eshop/store/<id:int>/<action:re:(inc|pri)>
@app.route('/admin/eshop/store/<id:int>/inc', method=state.METHOD_POST)
@app.route('/admin/eshop/store/<id:int>/pri', method=state.METHOD_POST)
def admin_item_incdec(req, id):
    check_login(req, '/log_in?referer=/admin/eshop/store/%s' % id)
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

    action = Action.bind(req.form, action_type)

    item = Item(id)
    if not item.action(req, action) or not item.get(req):
        req.status = state.HTTP_NOT_FOUND
        req.content_type = 'application/json'
        return json.dumps({'reason': 'item not found'})

    req.content_type = 'application/json'
    from pprint import pprint
    pprint(item.__dict__)
    return json.dumps({'item': item.__dict__})
# enddef


@app.route('/eshop')
def eshop_orders_eshop(req):
    do_check_mgc(req)
    pager = Pager()
    pager.bind(req.args)

    items = Item.list(req, pager, state=STATE_VISIBLE)
    return generate_page(req, "eshop/eshop.html",
                         token=create_token(req),
                         cfg_currency=req.cfg.eshop_currency,
                         pager=pager, items=items)


@app.route('/eshop/<id:int>')
def eshop_orders_detail(req, id):
    do_check_mgc(req)
    item = Item(id)
    if not item.get(req):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)
    item.attachments = Attachment.list(req, Pager(),
                                       object_type='eshop_item', object_id=id)
    return generate_page(req, "eshop/item_detail.html",
                         token=create_token(req),
                         item=item, cfg_currency=req.cfg.eshop_currency)
