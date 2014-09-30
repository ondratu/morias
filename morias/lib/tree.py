
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
                if self.next:
                    next = m._get_item(c, self.__class__, id = self.next)
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
        """ * set items's next to None and 0 order to time()
            * set prev's next to items's next or next.order to 0
            * set all items where parent = item to patent = item.parent

            * set prev's next to item or fix next's item order to not 0
            * update item (next = next, parent = next's parent)
        """

        m = driver(req)
        c = m._lock(req)                    # lock the table first

        try:
            new_next = self.next            # store new position
            m._get(self, c)                 # fresh item's data
            if self.next == new_next:
                m._rollback(c)
                return self                 # no moving :)

            # load new prev first, couse for move to and, there wold be two
            # next == null
            prev = m._get_item(c, self.__class__, next = new_next)

            tmp_next = self.next
            tmp_order = self.order
            ''' cut item from old position '''
            if tmp_next:
                self.next = None            # fix next to move is posible
            if tmp_order == 0:
                self.order = int(time())    # fix item is not first now
            if tmp_next or tmp_order == 0:
                m._mod(self, c)

            if tmp_order != 0:              # fix my prev item
                oprev = m._get_item(c, self.__class__, next = self.id)
                oprev.next = tmp_next
                m._mod(oprev, c)
            elif tmp_next:                  # fix nexts order to be first
                next = m._get_item(c, self.__class__, id = tmp_next)
                next.order = 0;
                m._mod(next, c)

            m._fix_parent(c, self.__class__, self.id, self.parent)  # fix item's child

            ''' push item to new position '''
            if new_next:                    # fix new parents
                next = m._get_item(c, self.__class__, id = new_next)
                self.parent = next.parent

            if prev is None:                # fix next, if is not first
                self.order = 0
                if new_next:                # fix nexts's order
                    next.order = int(time())
            else:                           # set prev's next
                if prev.id == tmp_next:
                    m._get(prev, c)         # fresh prev, couse could have order=0
                prev.next = self.id
                m._mod(prev, c)

            if new_next:
                m._mod(next, c)

            self.next = new_next
            m._mod(self, c)
            m._commit(c)
        except KeyError as e:
            m._rollback(c)
            return None
        return self
    # enddef move

    def to_child(self, req):
        m = driver(req)
        c = m._lock(req)                    # lock the table first

        try:
            m._get(self, c)                 # fresh item's data
            prev = m._get_item(c, self.__class__, next = self.id)
            if prev is None:
                m._rollback(c)
                return None                 # no moving :)

            if self.parent == prev.parent:
                self.parent = prev.id       # move to same lvl as prev
            else:
                self.parent = prev.parent   # be prev's child

            m._mod(self, c)
            m._commit(c)
        except KeyError as e:
            m._rollback(c)
            return None
        return self
    # enddef to_child

    def to_parent(self, req):
        m = driver(req)
        c = m._lock(req)                    # lock the table first

        try:
            m._get(self, c)                 # fresh item's data
            if self.parent is None:
                raise StopIteration("Item is at root")

            nparent = m._get_item(c, self.__class__, id = self.next) if self.next else None
            if self.parent == nparent:
                raise StopIteration("Can't be higher then next")

            # if item not on root, it must have parent
            self.parent = m._get_item(c, self.__class__, id = self.parent).parent
            m._mod(self, c)
            m._commit(c)
        except (KeyError, StopIteration) as e:
            m._rollback(c)
            return None
        return self
    # enddef to_parent

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
        _levels = {}

        _id, item = items.popitem(False)
        while item:
            item['_level'] = _levels[item[cls.PARENT]] + 1 if item[cls.PARENT] else 0
            _levels[item[cls.ID]] = item['_level']
            _sorted.append(item)
            item = items.pop(item[cls.NEXT], None)
        return _sorted
#endclass
