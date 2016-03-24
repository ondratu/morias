from falias.sqlite import DictCursor
from sqlite3 import IntegrityError

from morias.lib.redirects import Redirect


def test(req):
    with req.db.transaction(req.log_info, DictCursor) as c:
        c.execute("PRAGMA stats")
        c.execute(
            "SELECT id, src, dst, code, state FROM redirects LIMIT 1")


def get(self, req, key='id'):
    if key == 'id':
        value = self.id
    elif key == 'src':
        value = self.src
    else:
        raise RuntimeError('Only id or src could be use to get')

    tran = req.db.transaction(req.log_info)
    c = tran.cursor(DictCursor)
    c.execute("SELECT * FROM redirects WHERE %s = %%s" % key,
              value)
    row = c.fetchone()
    if not row:
        return None

    self.from_row(row)
    tran.commit()
    return self
# enddef


def add(self, req):
    tran = req.db.transaction(req.log_info)
    c = tran.cursor()
    try:
        c.execute("""
            INSERT INTO redirects (src, dst, code, state)
                VALUES (%s, %s, %d, %d)
            """, (self.src, self.dst, self.code, self.state))
        self.id = c.lastrowid
    except IntegrityError:
        req.log_error("Some key exist yet or some reference not")
        return None
    tran.commit()
    return self
# enddef


def mod(self, req):
    tran = req.db.transaction(req.log_info)
    c = tran.cursor()

    try:
        c.execute("""
            UPDATE redirects SET
                src=%s, dst=%s, code=%d, state=%d
            WHERE id = %d""", (self.src, self.dst, self.code, self.state,
                               self.id))
    except IntegrityError:
        req.log_error("Some key exist yet or some reference not")
        return False

    if not c.rowcount:
        return None

    tran.commit()
    return self
# enddef


def set_state(self, req, state):
    tran = req.db.transaction(req.log_info)
    c = tran.cursor()
    c.execute("UPDATE redirects SET state = %s WHERE id = %s",
              (state, self.id))

    if not c.rowcount:
        return None

    tran.commit()
    self.state = state
    return self
# enddef


def delete(self, req):
    tran = req.db.transaction(req.log_info)
    c = tran.cursor()
    c.execute("DELETE FROM redirects WHERE id = %s", self.id)

    if not c.rowcount:
        return None

    tran.commit()
    return self
# enddef


def item_list(req, pager, search=None, state=None):
    conds = []
    if search:
        value = search.replace("'", "''")
        conds.append("(src LIKE '%%{1}%%' OR dst LIKE '%%{1}%%')".format(
                     value, value))
    if state is not None:
        conds.append("state=%d" % state)
    cond = 'WHERE '+(' AND '.join(conds)) if conds else ''

    tran = req.db.transaction(req.log_info)
    c = tran.cursor(DictCursor)
    c.execute("SELECT * FROM redirects %s ORDER BY %s %s LIMIT %%d, %%d" %
              (cond, pager.order, pager.sort),
              (pager.offset, pager.limit))
    items = []
    for row in iter(c.fetchone, None):
        item = Redirect()
        item.from_row(row)
        items.append(item)

    c.execute("SELECT count(*) FROM redirects %s" % cond)
    pager.total = c.fetchone()['count(*)']

    tran.commit()
    return items
# enddef
