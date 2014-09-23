
from falias.util import nint
from time import time

# errors
EMPTY_TITLE     = 1

_drivers = ("sqlite",)

def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "tree_" + req.db.driver
    return __import__("lib." + m).__getattribute__(m)
#enddef

class Item(object):
    """ \ First Item (0)
        \ Item
        | \ Item
        | \ Item
        | Item
        | \ Item
        | | \ Item
        | \ Item
        \ Item
    """

    ID      = 'id'
    PARENT  = 'parent'
    NEXT    = 'next'
    ORDER   = 'order'
    TABLE   = 'tree'

    def __init__(self, id = None):
        self.id = id
        self.parent = None
        self.order = int(time())    # only one item in DB could be first
        self.next = None            # only one item in DB could be last

    def get(self, req):
        m = driver(req)
        return m.get(self, req)

    def add(self, req, **kwargs):
        """ * fix next's item order if there is not prev
            * create new item (parent as next's)
            * set prev's next to new item
            * set items's next to prev's next
        """
        m = driver(req)

        c = m._lock(req)                    # lock the table first
        try:
            # get preview item of me
            prev = m._get_item(c, self.__class__, next = self.next)
            if prev is None:                # fix next, if is not first
                self.order = 0
                next = m._get_item(c, self.__class__, id = self.next) if self.next else None
                if next:
                    next.order = int(time())
                    self.parent = next.parent
                    m._mod(next, c)

            tmp_next = self.next
            self.next = None
            m._add(self, c, **kwargs)       # add to db

            if prev:                        # set prev's next
                prev.next = self.id
                m._mod(prev, c)

            if tmp_next:                    # fix items's next
                self.next = tmp_next
                m._mod(self, c)

            m._commit(c)                    # release lock
        except KeyError as e:
            m._rollback(c)
            return None

        return self
    #enddef

    def mod(self, req, **kwargs):
        if not self.title: return EMPTY_TITLE
        m = driver(req)
        return m.mod(self, req, **kwargs)

    def delete(self, req):
        """ * set items's next to None
            * set prev's next to items's next or next.order to 0
            * set all items where parent = item to patent = item.parent
            * delete items's
        """
        m = driver(req)
        c = m._lock(req)                    # lock the table first

        try:
            m._get(self, c)                 # fresh item's data
            tmp_next = self.next
            tmp_order = self.order
            if tmp_next:                    # disable item's next
                self.next = None
                self.order = int(time())
                m._mod(self, c)

            if tmp_order != 0:             # fix my prev item
                prev = m._get_item(c, self.__class__, next = self.id)
                prev.next = tmp_next
                m._mod(prev, c)
            elif tmp_next:                  # fix nexts order to be first
                next = m._get_item(c, self.__class__, id = tmp_next)
                if next:
                    next.order = 0;
                    m._mod(next, c)

            m._fix_parent(c, self.__class__, self.id, self.parent)  # fix item's child

            m._del(self, c)                  # delete item
            m._commit(c)
        except KeyError as e:
            req.log_error(str(e))
            m._rollback(c)
            return None
        return True


    def move(self, req):        # TODO: move not work yet !
        """ * set items's next to None
            * set prev's next to items's next or next.order to 0
            * set all items where parent = item to patent = item.parent

            * set prev's next to item or fix next's item order to 0
            * update item (next = next, parent = next's parent)
        """

        m = driver(req)
        c = m._lock(req)                    # lock the table first

        try:
            # fix old position
            orig = m._get_item(c, self.__class__, id = self.id)
            if orig.order == 0:      # fix my prev
                prev = m._get_item(c, self.__class__, next = orig.id)
                prev.next = orig.next
                m._mod(prev, c)
            next = m._get_item(c, self.__class__, id = orig.next) if orig.next else None
            if next:                        # fix my next that is first
                if orig.order == 0:
                    next.order = 0
                    self.order = None
                if next.parent == self.id:  # my child have my parent as parent
                    next.parent = self.parent
                if orig.order == 0 or next.parent == self.id:
                    m._mod(next, c)

            # fix new position
            prev = m._get_item(c, self.__class__, next = self.next)
            next = m._get_item(c, self.__class__, id = self.next) if self.next else None
            if next:
                self.parent = next.parent
            if prev:                # fix my new prev
                prev.next = self.id
                m._mod(prev, c)
            elif self.next:         # fix my next that is not First
                next.order = None
                self.order = 0
                m.mod(next, c)

            m._mod(self.c)
            m._commit(c)
        except KeyError as e:
            m._rollback(c)
            return None
        return self
    # enddef move

    def bind(self, form):
        self.id = form.getfirst(self.ID, self.id, nint)
        self.next = form.getfirst(self.NEXT, None, nint)

    @staticmethod
    def list(req, cls, pager, **kwargs):
        pager.order = cls.ORDER if not pager.order else pager.order
        m = driver(req)
        return m.item_list(req, cls, pager, **kwargs)

    @staticmethod
    def full_tree(req, cls, **kwargs):
        m = driver(req)
        return Item.sort(cls, m.full_tree(req, cls, **kwargs))

    @staticmethod
    def sort(cls, items):
        if not items: return []
        _sorted = []

        _id, item = items.popitem(False)
        while item:
            _sorted.append(item)
            item = items.pop(item[cls.NEXT], None)
        return _sorted
#endclass
