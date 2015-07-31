""" This module is simple eshop-orders as admin modul for working with orders
    and simple module for shoping, resp. shoping cart.
    If you want to use your own transposition or payment, just create your own
    module, with eshop your transportation config option and use your own
    shopping_address.html template.
"""

from poorwsgi import *
from falias.sql import Sql
from falias.util import nint, Object
from falias.smtp import Smtp

import json

from core.login import rights, check_login, check_right, check_referer, \
                        do_check_login
from core.render import generate_page, morias_template

from lib.menu import Item as MenuItem
from lib.pager import Pager
from lib.login import re_email
from lib.eshop_orders import ShoppingCart, Address, Order, \
            STATE_STORNED, STATE_ACCEPT, STATE_PROCESS, STATE_SENT, STATE_CLOSED, \
            STATE_WAIT_FOR_PAID, STATE_WAIT_FOR_PICK_UP, \
            EMPTY_ITEMS, NOT_ENOUGH_ITEMS
from lib.eshop_store import Item, STATE_VISIBLE

from eshop import eshop_menu
from user import user_sections, user_info_menu

_fee_doc = "-1 to disable, or any other value to enable 0 means no fee"
_check_conf = (
    # morias common block
    ('morias', 'db', Sql),
    ('morias', 'smtp',Smtp),
    # common addresses block
    ('addresses', 'region',     bool, False, True),
    ('addresses', 'country',    bool, False, True),
    # eshop block
    ('eshop', 'cart_in_menu',   bool, True),
    # transportation block (-1 to disable)
    ('eshop', 'transportation_post',        int, 0, True, _fee_doc),
    ('eshop', 'transportation_personally',  int, 0, True, _fee_doc),
    ('eshop', 'transportation_haulier',     int, 0, True, _fee_doc),
    ('eshop', 'transportation_messenger',   int, 0, True, _fee_doc),
    # paymant block (-1 to disable)
    ('eshop', 'payment_delivery',           int, 0, True, _fee_doc),
    ('eshop', 'payment_pickup',             int, 0, True, _fee_doc),
    ('eshop', 'payment_transfer',           int, 0, True, _fee_doc),
    ('eshop', 'payment_card',               int, 0, True, _fee_doc),
    ('eshop', 'payment_paypal',             int, 0, True, _fee_doc),
)

def _call_conf(cfg, parser):
    cfg.footers.append('eshop/_footer.html')
    if cfg.eshop_cart_in_menu:
        user_sections.append(MenuItem('/eshop/cart', label="Shopping Cart",
                        symbol="shopping-cart", role="shopping-cart"))
    if cfg.debug:
        app.set_route('/eshop/cart/wipe', eshop_cart_wipe)
#enddef

module_right = 'eshop_orders'
rights.add(module_right)

eshop_menu.append(MenuItem('/admin/eshop/orders', label="Orders",
                        symbol="eshop-orders", rights = [module_right]))
user_info_menu.append(MenuItem('/eshop/orders', label="My Orders",
                        symbol="eshop-orders"))

def send_order_status(req, order):
    try:
        req.log_error('posilam mail......')
        # TODO: use lang from cart when order was create
        req.smtp.send_email_alternative(
                morias_template(req,
                                'mail/eshop/order_subject.jinja',
                                order = order).encode('utf-8'),  # subject
                order.email,
                morias_template(req,
                                'mail/eshop/order.jinja',
                                order = order).encode('utf-8'),  # body
                morias_template(req,
                                'mail/eshop/order.html',
                                order = order).encode('utf-8'),  # body
                logger = req.logger)
    #except Exception as e:
    #    req.log_error('Mailing order[%d] error: %s' % (order.id, str(e)),
    #                    state.LOG_ERR)
    finally:
        pass
#enddef

@app.route('/eshop/cart', method = state.METHOD_GET | state.METHOD_PATCH)
def eshop_cart(req):
    cart = ShoppingCart(req)

    if req.method == 'PATCH':
        cart.merge_items(req.json.get('items', []))
        req.content_type = 'application/json'
        cart.store(req)     # store shopping cart
        cart.calculate()
        return json.dumps({ 'cart': cart.dict() })

    cart.calculate()
    if req.is_xhr:
        req.content_type = 'application/json'
        return json.dumps({ 'cart': cart.dict() })

    # GET method only view shopping cart - no store was needed
    return generate_page(req, "eshop/shopping_cart.html",
                        cfg_currency = req.cfg.eshop_currency,
                        cart = cart )
#enddef

@app.route('/eshop/cart/add', method = state.METHOD_PUT)
def eshop_cart_add(req):
    cart = ShoppingCart(req)

    item_id = req.json.getfirst('item_id', fce=nint)
    count   = req.json.getfirst('count', 0, int)
    if count < 1:
        req.state = state.HTTP_BAD_REQUEST
        req.content_type = 'application/json'
        return json.dumps({'reason': 'count must bigger then zero'})

    item = Item(item_id)
    if not item.get(req) or item.state != STATE_VISIBLE:
        req.state = state.HTTP_NOT_FOUND
        req.content_type = 'application/json'
        return json.dumps({'reason': 'item not found'})

    # append or incrase item
    cart.merge_items(((item_id, {
                'name'  : item.name,
                'price' : item.price,
                'count' : count
            }),))
    cart.store(req)
    cart.calculate()
    req.content_type = 'application/json'
    return json.dumps({'reason': 'item append to cart', 'cart': cart.dict() })
#enddef

def eshop_cart_wipe(req):
    """ /eshop/cart/wipe - wipe esho cart - for debug only """
    do_check_login(req)
    cart = ShoppingCart(req)
    cart.clean(req)
    redirect(req, '/eshop/cart')
#enddef

@app.route('/eshop/cart/address')
def eshop_cart_address(req, cart = None, error = None):
    cart = cart or ShoppingCart(req)

    # get method returns HTML Form
    cfg = Object()
    cfg.addresses_country   = req.cfg.addresses_country
    cfg.addresses_region    = req.cfg.addresses_region
    cfg.eshop_currency      = req.cfg.eshop_currency
    # all defined transportation (for universal use):
    for key, val in req.cfg.__dict__.items():
        if key.startswith('eshop_transportation_'):
            cfg.__dict__[key[6:]] = val
        elif key.startswith('eshop_payment_'):
            cfg.__dict__[key[6:]] = val

    # GET method only view shopping cart - no store was needed
    return generate_page(req, "eshop/shopping_address.html",
                        cfg = cfg, cart = cart, error = error )
#enddef

@app.route('/eshop/cart/address', method = state.METHOD_POST)
def eshop_cart_address_post(req):
    cart = ShoppingCart(req)

    way             = req.form.getfirst('way', '', str)
    same_as_billing = 'same_as_billing' in req.form
    billing_address = Address.bind(req.form, 'billing_')
    if same_as_billing:
        shipping_address = billing_address.copy()
        shipping_address['same_as_billing'] = True
    else:
        shipping_address = Address.bind(req.form, 'shipping')
        shipping_address['same_as_billing'] = False
    transportation  = req.form.getfirst('transportation', '', str)
    payment         = req.form.getfirst('payment', '', str)
    email           = req.form.getfirst('email', '', str)

    transportation_price = req.cfg.__dict__.get(
                'eshop_transportation_' + transportation, -1)
    payment_price = req.cfg.__dict__.get(
                'eshop_payment_' + payment, -1)

    if transportation and transportation_price < 0:
        raise SERVER_RETURN(state.HTTP_BAD_REQUEST)
    if payment and payment_price < 0:
        raise SERVER_RETURN(state.HTTP_BAD_REQUEST)

    if len(billing_address):
        cart.billing_address = billing_address
    if len(shipping_address):
        cart.shipping_address = shipping_address
    if transportation:
        cart.transportation = (transportation, transportation_price)
    if payment:
        cart.payment = (payment, payment_price)
    if re_email.match(email):
        cart.email = email

    cart.store(req)     # store shopping cart

    if not billing_address:
        return eshop_cart_address(req, cart, error = 'no_billing_address')
    if len(shipping_address) == 1:  # only same_as_billing
        return eshop_cart_address(req, cart, error = 'no_shipping_address')
    if not transportation:
        return eshop_cart_address(req, cart, error = 'no_transportation')
    if not payment:
        return eshop_cart_address(req, cart, error = 'no_payment')
    if not email:
        return eshop_cart_address(req, cart, error = 'no_email')
    # end of errors block

    cart.calculate()

    if way == 'next':
        redirect(req, '/eshop/cart/recapitulation')
    elif way == 'prev':
        redirect(req, '/eshop/cart')
    return eshop_cart_address(req, cart)
# enddef POST method


@app.route('/eshop/cart/recapitulation')
def eshop_cart_recapitulation(req):
    cart = ShoppingCart(req)
    cart.calculate()

    # get method returns HTML Form
    cfg = Object()
    cfg.addresses_country   = req.cfg.addresses_country
    cfg.addresses_region    = req.cfg.addresses_region
    cfg.eshop_currency      = req.cfg.eshop_currency
    # all defined transportation (for universal use):
    for key, val in req.cfg.__dict__.items():
        if key.startswith('eshop_transportation_'):
            cfg.__dict__[key[6:]] = val
        elif key.startswith('eshop_payment_'):
            cfg.__dict__[key[6:]] = val

    # GET method only view shopping cart - no store was needed
    return generate_page(req, "eshop/shopping_recapitulation.html",
                        cfg = cfg, cart = cart )
# enddef /eshop/cart/recapitulation

@app.route('/eshop/cart/pay_and_order')
def eshop_cart_pay_and_order(req):
    cart = ShoppingCart(req)
    #TODO: payment page if could be (paypal, card, transfer)
    order = Order.from_cart(cart)
    if not order:
        redirect(req, '/eshop')
    order.client_id = req.login.id if req.login else None
    retval = order.add(req)
    if retval == order:
        cart.clean(req)
        send_order_status(req, order)
        redirect(req, '/eshop')
    if retval[0] == EMPTY_ITEMS:
        redirect(req, '/eshop')
    if retval[0] == NOT_ENOUGH_ITEMS:
        cart.set_not_enought(retval[1])
        cart.store(req)
        redirect(req, '/eshop/cart')
#enddef /eshop/cart/pay_and_order

@app.route('/eshop/orders')
def user_orders(req):
    check_login(req)

    state = req.args.getfirst('state', -1, int)

    kwargs = {'client_id': req.login.id}
    if state >= 0:
        kwargs['state'] = state

    pager = Pager(sort = 'desc')
    items = Order.list(req, pager, **kwargs)

    return generate_page(req, "/eshop/orders.html",
                         pager = pager, items = items,
                         state = state)
#enddef

@app.route('/eshop/orders/<id:int>')
def user_orders_detail(req, id):
    check_login(req)
    check_right(req, module_right)

    order = Order(id)
    if order.get(req) is None:
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)
    if order.client_id != req.login.id:
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)

    cfg = Object()
    cfg.addresses_country   = req.cfg.addresses_country
    cfg.addresses_region    = req.cfg.addresses_region
    cfg.eshop_currency      = req.cfg.eshop_currency

    order.calculate()
    return generate_page(req, "eshop/orders_detail.html",
                         order = order, cfg = cfg)
#enddef

@app.route('/eshop/orders/<id:int>/storno', method = state.METHOD_POST)
def user_orders_storno(req, id):
    check_login(req)
    check_referer(req, '/eshop/orders/%d' % id)

    message = req.form.getfirst('message', '', uni)

    order = Order(id)
    if order.get(req) is None:
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)
    if order.client_id != req.login.id:
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)

    if order.set_state(req, STATE_STORNED, usernote = message) is None:
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    send_order_status(req, order)
    redirect(req, '/eshop/orders/%d' % id)
#enddef

@app.route('/admin/eshop/orders')
def admin_orders(req):
    check_login(req)
    check_right(req, module_right)

    state = req.args.getfirst('state', -1, int)
    client = req.args.getfirst('client', '', uni)

    kwargs = {}
    if state >= 0:
        kwargs['state'] = state
    if client:
        kwargs['client'] = client

    pager = Pager(sort = 'desc')
    items = Order.list(req, pager, **kwargs)

    return generate_page(req, "admin/eshop/orders.html",
                        pager = pager, items = items,
                        state = state, client = client)
#enddef

@app.route('/admin/eshop/orders/<id:int>')
def admin_orders_mod(req, id):
    check_login(req)
    check_right(req, module_right)

    order = Order(id)
    if order.get(req) is None:
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    cfg = Object()
    cfg.addresses_country   = req.cfg.addresses_country
    cfg.addresses_region    = req.cfg.addresses_region
    cfg.eshop_currency      = req.cfg.eshop_currency

    order.calculate()
    return generate_page(req, "admin/eshop/orders_mod.html", order = order,
                        cfg = cfg)
#enddef

@app.route('/admin/eshop/orders/<id:int>/storno', method = state.METHOD_POST)
@app.route('/admin/eshop/orders/<id:int>/wait_for_paid', method = state.METHOD_POST)
@app.route('/admin/eshop/orders/<id:int>/process', method = state.METHOD_POST)
@app.route('/admin/eshop/orders/<id:int>/sent', method = state.METHOD_POST)
@app.route('/admin/eshop/orders/<id:int>/wait_for_pick_up', method = state.METHOD_POST)
@app.route('/admin/eshop/orders/<id:int>/close', method = state.METHOD_POST)
def admin_orders_action(req, id):
    check_login(req)
    check_referer(req, '/admin/eshop/orders/%d' % id)
    check_right(req, module_right)

    if req.uri.endswith('/storno'):
        ostate = STATE_STORNED
    elif req.uri.endswith('/process'):
        ostate = STATE_PROCESS
    elif req.uri.endswith('/sent'):
        ostate = STATE_SENT
    elif req.uri.endswith('/close'):
        ostate = STATE_CLOSED
    elif req.uri.endswith('/wait_for_paid'):
        ostate = STATE_WAIT_FOR_PAID
    elif req.uri.endswith('/wait_for_pick_up'):
        ostate = STATE_WAIT_FOR_PICK_UP
    else:
        raise SERVER_RETURN(state.HTTP_BAD_REQUEST)

    note = req.form.getfirst('note', '', uni)

    order = Order(id)
    if order.set_state(req, ostate, note) is None:
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    if ostate != STATE_CLOSED:
        send_order_status(req, order)

    redirect(req, '/admin/eshop/orders/%d' % id)
#enddef
