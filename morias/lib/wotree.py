
_drivers = ("sqlite",)


def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "wotree_" + req.db.driver
    return __import__("morias.lib." + m).lib.__getattribute__(m)


class WoItem(object):
    """Write only tree.

    This tree implement string base algorithm for tree, which is
    still sort from root to time branches. It is great for discussions.

    \ Item      1
    | Item      2
    | | Item    2.1
    | \ Item    2.2
    | Item      3
    | | Item    3.1
    | | | Item  3.1.1
    | \ Item    3.2
    \ Item      4
    """

    ID = 'id'
    TABLE = 'wotree'

    def __init__(self, id=None):
        self.id = id

    def get(self, req, **cond):
        m = driver(req)
        return m.get(self, req, **cond)

    def _last(self, req, c, parent, **cond):
        m = driver(req)
        return m._last(c, self.__class__, parent, **cond)

    def add(self, req, parent='', **kwargs):
        """Append new item to table"""
        m = driver(req)
        c = m._lock(req)        # need lock table to write
        try:
            last_id = self._last(req, c, parent)
            if parent and len(parent) <= len(last_id):
                # if strip last_id from parent, we need only sub-id
                last_id = last_id[len(parent)+1:]

            # increment last sub-id
            next_id = '%s' % (int(last_id, 16)+1) if last_id else '1'
            self.id = '%s.%s' % (parent, next_id) if parent else next_id

            m._add(self, c, **kwargs)
            m._commit(c)
        except KeyError as e:
            req.log_error(e)
            m._rollback(c)
            return None
        return self

    def mod(self, req, **kwargs):
        m = driver(req)
        return m.mod(self, req, **kwargs)

    def delete(self, req):
        m = driver(req)
        return m.delete(self, req)

    @staticmethod
    def list(req, cls, pager, **kwargs):
        pager.order = cls.ID if not pager.order else pager.order
        m = driver(req)
        return m.item_list(req, cls, pager, **kwargs)

    @staticmethod
    def test(req):
        m = driver(req)
        return m.test(req)
# endclass
