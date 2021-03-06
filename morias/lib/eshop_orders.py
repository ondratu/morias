
from falias.util import uni, dict_difference
from poorwsgi.session import PoorSession
from poorwsgi.state import LOG_INFO
from collections import OrderedDict
from time import time

from eshop_store import Item, Action

# states
STATE_STORNED = 0
STATE_ACCEPT = 1
STATE_PROCESS = 2
STATE_SENT = 3
STATE_CLOSED = 4

STATE_WAIT_FOR_PAID = 10
STATE_WAIT_FOR_PICK_UP = 11

EMPTY_EMAIL = 1
EMPTY_ITEMS = 2
NOT_ENOUGH_ITEMS = 3

_drivers = ("sqlite",)


def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "eshop_orders_" + req.db.driver
    return __import__("lib." + m).__getattribute__(m)


class ShoppingCart(object):
    def __init__(self, req):
        # Morias Eshop Orders Shopping Cart
        self.cookie = PoorSession(req, SID='MEOSC')
        shopping_cart = self.cookie.data.get('shopping_cart', {})
        self.items = shopping_cart.get('items', [])
        self.billing_address = shopping_cart.get('billing_address', {})
        self.shipping_address = shopping_cart.get('shipping_address', {})
        self.transportation = shopping_cart.get('transportation', None)
        self.payment = shopping_cart.get('payment', None)
        self.email = shopping_cart.get('email', '')
        self.emailcheck = shopping_cart.get('emailcheck', '')
        self.message = shopping_cart.get('message', '')

        if req.login:
            self._merge_properties(req.login.data.get('shopping_cart', {}),
                                   self.email or req.login.email)

            if self.cookie.data.get('stored', False):
                # if data is merged from cookie, store data to login
                # and clean the cookie
                self.store(req)
                self.cookie.destroy()
                self.cookie.header(req, req.headers_out)
    # enddef

    def _merge_properties(self, cart, email):
        billing_address = cart.get('billing_address', {})
        shipping_address = cart.get('shipping_address', {})
        transportation = cart.get('transportation', None)
        payment = cart.get('payment', None)
        message = cart.get('message', None)

        self.merge_items(cart.get('items', []))
        if len(billing_address):
            self.billing_address = billing_address
        if len(shipping_address):
            self.shipping_address = shipping_address
        if transportation is not None:
            self.transportation = transportation
        if payment is not None:
            self.payment = payment
        self.email = cart.get('email', email)
        if message is not None:
            self.message = message
    # enddef

    def merge_items(self, items):
        tmp = OrderedDict(self.items)
        for item_id, item in items:
            if item_id in tmp:
                tmp[item_id]['count'] += item['count']
                if tmp[item_id]['count'] <= 0:
                    tmp.pop(item_id)   # remove zero less count items
                elif item['count'] < 0:
                    tmp[item_id].pop('not_enough', False)
            else:
                tmp[item_id] = item
        # endfor

        self.items = tmp.items()
    # enddef

    def set_not_enought(self, ids):
        for item_id, item in self.items:
            if item_id in ids:
                item['not_enough'] = True
            else:
                item['not_enough'] = False
    # enddef

    def store(self, req):
        if req.login:
            req.log_error('storing user data', LOG_INFO)
            req.login._mod(req, ['data'], [{'shopping_cart': self.dict()}])
        else:
            req.log_error('Sendig shopping_cart cookie....', LOG_INFO)
            self.cookie.data['shopping_cart'] = self.dict()
            self.cookie.data['stored'] = True
            self.cookie.header(req, req.headers_out)
    # enddef

    def dict(self):
        return dict((k, v) for k, v in self.__dict__.items() if k != 'cookie')

    def calculate(self):
        self.count = 0                          # count of all items in cart
        self.summary = 0                        # summary price of all items
        for item_id, item in self.items:
            item['summary'] = item['count'] * item['price']
            self.count += item['count']
            self.summary += item['summary']

        self.total = self.summary               # total price of order
        if self.transportation:                 # transportation price
            self.total += self.transportation[1]
        if self.payment:                        # payment price
            self.total += self.payment[1]
    # enddef

    def clean(self, req):
        if req.login:
            req.log_error('storing user data - cleaning shopping_cart ')
            req.login._mod(req, ['data'], [{'shopping_cart': {}}])
        else:
            req.log_error('cleaning shopping_cart cookie....')
            self.cookie.destroy()
            self.cookie.header(req, req.headers_out)

        self.items = []
        self.billing_address = {}
        self.shipping_address = {}
        self.transportation = None
        self.payment = None
        self.email = ''
        self.emailcheck = ''
        self.message = ''
# endclass


class Address(object):
    @staticmethod
    def bind(form, prefix):
        rv = {'name':       form.getfirst(prefix+'name', '', uni),
              'address1':   form.getfirst(prefix+'address1', '', uni),
              'address2':   form.getfirst(prefix+'address2', '', uni),
              'city':       form.getfirst(prefix+'city', '', uni),
              'region':     form.getfirst(prefix+'region', '', uni),
              'zip':        form.getfirst(prefix+'zip', '', uni),
              'country':    form.getfirst(prefix+'country', '', uni)}
        return dict((k, v.strip()) for k, v in rv.items() if v.strip() != '')


class Order(object):
    def __init__(self, id=None):
        self.id = id
        self.state = STATE_ACCEPT
        self.email = None
        self.items = tuple()
        self.history = tuple()
        self.data = {}

    def calculate(self):
        self.count = 0                          # count of all items in cart
        self.summary = 0                        # summary price of all items
        for item_id, item in self.items:
            item['summary'] = item['count'] * item['price']
            self.count += item['count']
            self.summary += item['summary']

        self.total = self.summary                       # total price of order
        self.total += self.data.get('transportation', ('', 0))[1]
        self.total += self.data.get('payment', ('', 0))[1]
    # enddef

    @staticmethod
    def from_cart(cart):
        cart.calculate()
        if cart.count == 0:
            return None         # empty cart - no order

        order = Order()
        order.items = cart.items
        order.email = cart.email
        order.data = {
            'billing_address':  cart.billing_address,
            'shipping_address': cart.shipping_address,
            'transportation':   cart.transportation,
            'payment':          cart.payment,
            'message':          cart.message}
        return order
    # enddef

    def get(self, req):
        m = driver(req)
        return m.get(self, req)

    def add(self, req):
        if not self.items:
            return (EMPTY_ITEMS, 0)

        m = driver(req)
        c = m._lock(req)                        # lock database first
        not_enought_items = []
        try:
            m._add(self, c)                     # get id
            for item_id, it in self.items:   # record to store
                item = Item(item_id)
                action = Action.from_order(self.id, it['count'])
                try:
                    if item._action(req, c, action) is None:
                        raise RuntimeError('Item not found')
                except ValueError as e:
                    not_enought_items.append(e.args[1])
            if not_enought_items:
                m._rollback(c)
                return (NOT_ENOUGH_ITEMS, not_enought_items)
        except BaseException as e:
            m._rollback(c)
            return None
        m._commit(c)
        return self
    # enddef

    def mod(self, req, note=''):
        m = driver(req)
        c = m._lock(req)        # lock the table first

        try:
            new_state = self.state  # backup new data which could be change
            new_email = self.email
            new_items = self.items
            new_data = self.data

            if m._get(self, c) is None:
                raise LookupError('not found in backend')

            record = []
            if note:
                record.append(('note', note))
            if self.state != new_state:
                record.append((self.state, new_state))
                self.state = new_state
            if self.email != new_email:
                record.append((self.email, new_email))
                self.email = new_email
            if self.items != new_items:
                o_items = set(self.items)
                n_items = set(new_items)
                record.append((o_items.difference(n_items),    # removed items
                               n_items.difference(o_items)))   # appended items
                self.items = new_items

            if self.data != new_data:
                # removed items and appended items
                record.append((dict_difference(self.data, new_data),
                               dict_difference(new_data, self.data)))
                self.data = new_data

            self.history.append((int(time()), record))

            if m._mod(self, c) is None:
                raise LookupError('not found in backend')
        except Exception as e:
            req.log_error(str(e))
            m._rollback(c)
            return None

        m._commit(c)
        return self
    # enddef

    def set_state(self, req, state, note='', usernote=''):
        m = driver(req)
        c = m._lock(req)        # lock the table first

        try:
            if m._get(self, c) is None:
                raise LookupError('not found in backend')

            record = [(self.state, state)]
            self.state = state

            if note:
                record.append(('note', note))          # append storno note
            if usernote:
                record.append(('usernote', usernote))  # append storno usernote

            self.history.append((int(time()), record))

            if m._mod(self, c) is None:
                raise LookupError('not found in backend')

            if state == STATE_STORNED:          # "return" items to store
                for item_id, it in self.items:
                    item = Item(item_id)
                    action = Action.from_order(self.id, -it['count'])
                    if item._action(req, c, action) is None:
                        raise RuntimeError('Item not found')
            # endif

        except Exception as e:
            req.log_error(str(e))
            m._rollback(c)
            return None

        m._commit(c)
        return self
    # enddef

    @staticmethod
    def list(req, pager, **kwargs):
        allowed = ('order_id', 'client_id', 'modify_date', 'state')
        if pager.order not in allowed:
            pager.order = 'modify_date'
        m = driver(req)
        return m.item_list(req, pager, **kwargs)
# endclass
