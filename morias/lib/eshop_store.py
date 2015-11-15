
from falias.util import uni, nint

# actions
ACTION_INC = 1
ACTION_DEC = 2
ACTION_PRI = 3

# states
STATE_DISABLED = 0
STATE_VISIBLE = 1
STATE_HIDDEN = 2

# errrors
EMPTY_NAME = 1

_drivers = ("sqlite",)


def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "eshop_store_" + req.db.driver
    return __import__("lib." + m).__getattribute__(m)


class Item(object):
    def __init__(self, id=None):
        self.id = id
        self.state = STATE_HIDDEN

    def get(self, req):
        m = driver(req)
        return m.get(self, req)

    def add(self, req):
        if not self.name:
            return EMPTY_NAME

        m = driver(req)
        return m.add(self, req)
    # enddef

    def mod(self, req):
        if not self.name:
            return EMPTY_NAME

        m = driver(req)
        return m.mod(self, req)
    # enddef

    def set_state(self, req, state):
        m = driver(req)
        return m.set_state(self, req, state)

    def _action(self, req, c, action):
        m = driver(req)
        return m._action(self, c, action)

    def action(self, req, action):
        m = driver(req)
        return m.action(self, req, action)

    def bind(self, form):
        self.id = form.getfirst('item_id', self.id, nint)
        self.name = form.getfirst('name', '', uni)
        self.description = form.getfirst('description', '', uni)
        self.state = form.getfirst('state', STATE_HIDDEN, int)

        self.data = {}
    # enddef

    # TODO: dumps method

    @staticmethod
    def list(req, pager, **kwargs):
        if pager.order not in ('modify_date', 'name', 'count', 'price'):
            pager.order = 'modify_date'

        m = driver(req)
        return m.item_list(req, pager, **kwargs)
    # enddef
# endclass


class Action(object):
    @staticmethod
    def bind(form, action_type):
        action = Action()
        action.action_type = action_type
        action.data = {'note': form.getfirst('note', '', uni)}
        if action_type in (ACTION_INC, ACTION_DEC):
            action.data['count'] = form.getfirst('count', 0, int)
        if action_type == ACTION_PRI:
            action.data['price'] = form.getfirst('price', 0, float)
        return action
    # enddef

    @staticmethod
    def from_order(order_id, count):
        action = Action()
        action.action_type = ACTION_DEC
        action.data = {'count': count,
                       'order': order_id,
                       'note': '@ordered'}
        return action

    @staticmethod
    def list(req, pager, **kwargs):
        if pager.order not in ('timestamp', 'action_type'):
            pager.order = 'timestamp'

        m = driver(req)
        return m.item_list_actions(req, pager, **kwargs)
# endclass
