
from falias.util import islistable
from falias.sqlite import DictCursor
from sqlite3 import IntegrityError

from json import dumps, loads

from lib.articles import Article, Tag


def test(req):
    with req.db.transaction(req.log_info, DictCursor) as c:
        c.execute("PRAGMA stats")
        c.execute("SELECT strftime('%s','2013-12-09 18:19')*1")
        value = c.fetchone()[0]
        assert value == 1386613140
        c.execute("""
            SELECT article_id, serial_id, author_id, create_date, public_date,
                title, locale, perex, body, format, state, data
            FROM articles LIMIT 1
            """)


def get(self, req, key='article_id'):
    if key == 'article_id':
        value = self.id
    elif key == 'uri':
        value = self.uri
    else:
        raise RuntimeError('Only article_id or title could be use to get')

    tran = req.db.transaction(req.log_info)
    c = tran.cursor(DictCursor)
    c.execute("""
        SELECT *, email, l.name AS author FROM articles A
            JOIN logins l ON (a.author_id = l.login_id) WHERE %s = %%s LIMIT 1
        """ % key, value)
    row = c.fetchone()
    if not row:
        return None

    self.from_row(row)

    self.tags = []      # load tags
    c.execute("""
        SELECT a.tag_id, t.name
        FROM articles_tags a JOIN tags t ON (a.tag_id = t.tag_id)
        WHERE a.article_id = %s
        """, self.id)
    for row in c:
        req.log_debug(repr(row))
        self.tags.append(Tag(row[0], row[1]))

    tran.commit()
    return self
# enddef


def add(self, req):
    tran = req.db.transaction(req.log_info)
    c = tran.cursor()

    if self.public:
        public_sql = ('public_date, ', "strftime('%%s','now')*1, ")
    else:
        public_sql = ('', '')

    try:
        c.execute("""
            INSERT INTO articles
                (serial_id, author_id, create_date, {0}title, uri, locale,
                 perex, body, format, state, data)
            VALUES (%s, %s, strftime('%%s','now')*1, {1}%s, %s,
                 %s, %s, %s, %s, %s, %s)
            """.format(*public_sql),
                  (self.serial_id, self.author_id, self.title, self.uri,
                   self.locale, self.perex, self.body, self.format, self.state,
                   dumps(self.data)))
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

    public_sql = ''
    if self.public:
        public_sql = "public_date=strftime('%%s','now')*1, "

    try:
        c.execute("""
            UPDATE articles SET
                serial_id=%s, {0}title=%s, uri=%s, locale=%s, perex=%s,
                    body=%s, format=%s, state=%s, data=%s
                WHERE article_id = %s
            """.format(public_sql),
                  (self.serial_id, self.title, self.uri, self.locale,
                   self.perex, self.body, self.format, self.state,
                   dumps(self.data), self.id))
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
    c.execute("UPDATE articles SET state = %s WHERE article_id = %s",
              (state, self.id))

    if not c.rowcount:
        return None

    tran.commit()
    self.state = state
    return self
# enddef


def inc_data_key(self, req, key='article_id', **kwargs):
    if key == 'article_id':
        value = self.id
    elif key == 'uri':
        value = self.uri
    else:
        raise RuntimeError('Only article_id or title could be use to get')

    tran = req.db.transaction(req.log_info)
    c = tran.cursor()
    c.execute("SELECT article_id, data FROM articles WHERE %s = %%s LIMIT 1" %
              key, value)
    row = c.fetchone()
    if not row:
        return None

    article_id, data = row[0], loads(row[1])
    for k, v in kwargs.items():
        data[k] = data.get(k, 0) + v
    c.execute("UPDATE articles SET data = %s WHERE article_id = %d",
              (dumps(data), article_id))
    tran.commit()
    return True
# enddef


def append_tag(self, req, tag_id):
    with req.db.transaction(req.log_info) as c:
        try:
            c.execute("""
                INSERT INTO articles_tags (article_id, tag_id)
                VALUES (%s, %s)""", (self.id, tag_id))
        except IntegrityError:
            req.log_error("Some key exist yet or some reference not")
            return False
    return True
# enddef


def remove_tag(self, req, tag_id):
    with req.db.transaction(req.log_info) as c:
        c.execute("""
            DELETE FROM articles_tags
            WHERE article_id = %s AND tag_id= %s""", (self.id, tag_id))
# enddef


def tags_list(req, id):
    with req.db.transaction(req.log_info) as c:
        c.execute("""
            SELECT a.tag_id, t.name
            FROM articles_tags a JOIN tags t ON (a.tag_id = t.tag_id)
            WHERE a.article_id = %s
            """, id)
        return list(Tag(row[0], row[1]) for row in c)


def item_list(req, pager, perex=False, **kwargs):
    perex = ', perex ' if perex else ''
    join = ''

    public = kwargs.pop('public', False)
    tag = kwargs.pop('tag', None)
    if tag:
        kwargs['t.name'] = tag
        join = """
            JOIN articles_tags at ON (at.article_id = a.article_id)
            JOIN tags t ON (t.tag_id = at.tag_id)
        """

    keys = list("%s %s %%s" % (k, 'in' if islistable(v) else '=')
                for k, v in kwargs.items())
    if public:       # public is alias key
        keys.append("public_date > 0")
        keys.append("state != 0")

    cond = "WHERE " + ' AND '.join(keys) if keys else ''

    tran = req.db.transaction(req.log_info)
    c = tran.cursor(DictCursor)
    c.execute("""
        SELECT a.article_id, serial_id, author_id, email, name AS author,
            create_date, public_date, title, uri, locale, state %s
        FROM articles a JOIN logins l ON (a.author_id = l.login_id)
            %s %s
            ORDER BY %s %s LIMIT %%s, %%s
        """ % (perex, join, cond, pager.order, pager.sort),
              tuple(kwargs.values()) + (pager.offset, pager.limit))
    items = []
    for row in iter(c.fetchone, None):
        item = Article()
        item.from_row(row)
        items.append(item)
    # endwhile

    c.execute("SELECT count(*) FROM articles a %s %s" % (join, cond),
              kwargs.values())
    pager.total = c.fetchone()['count(*)']
    tran.commit()

    return items
# enddef
