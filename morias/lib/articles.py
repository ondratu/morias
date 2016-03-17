from falias.util import uni, nint, Object
from unidecode import unidecode

from datetime import datetime
from re import sub

import json

from discussion import Comment

# errors
EMPTY_TITLE = 1
EMPTY_PEREX = 2
EMPTY_BODY = 3

FORMAT_HTML = 1
FORMAT_RST = 2

_drivers = ("sqlite",)


def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "articles_" + req.db.driver
    return __import__("lib." + m).__getattribute__(m)


class ArticleComment(Comment, Object):
    TABLE = 'articles_discussion'
    OBJECT_ID = 'article_id'

    def __json__(self):
        rv = super(ArticleComment, self).__json__()
        dt = rv['create_date']
        rv['create_date'] = (dt.year, dt.month, dt.day, dt.hour, dt.minute,
                             dt.second)
        return rv

    @staticmethod
    def list(req, article_id, pager, **kwargs):
        return Comment.list(req, ArticleComment, article_id, pager, **kwargs)


class Tag(Object):
    def __init__(self, id, value):
        super(Tag, self).__init__(id=id, value=value)


class Article(object):
    def __init__(self, id=None):
        self.id = id

    def from_row(self, row):
        for key in row.keys():
            val = row[key]
            if key == 'article_id':
                self.id = val
            elif key == 'create_date':
                self.create_date = datetime.fromtimestamp(val)
            elif key == 'public_date':
                self.public_date = datetime.fromtimestamp(val)
            elif key == 'data':
                self.data = json.loads(val)
            else:
                setattr(self, key, val)
    # enddef

    def get(self, req, key='article_id'):
        m = driver(req)
        return m.get(self, req, key)

    def add(self, req):
        if not self.title:
            return EMPTY_TITLE
        if not self.perex:
            return EMPTY_PEREX
        if not self.body:
            return EMPTY_BODY
        m = driver(req)
        m.add(self, req)
    # enddef

    def mod(self, req):
        if not self.title:
            return EMPTY_TITLE
        if not self.perex:
            return EMPTY_PEREX
        if not self.body:
            return EMPTY_BODY
        m = driver(req)
        return m.mod(self, req)
    # enddef

    def set_state(self, req, state):
        m = driver(req)
        return m.set_state(self, req, state)

    def inc_data_key(self, req, key='article_id', **kwargs):
        m = driver(req)
        return m.inc_data_key(self, req, key, **kwargs)

    def bind(self, form, author_id=None):
        self.id = form.getfirst('article_id', self.id, nint)
        self.serial_id = form.getfirst('serial_id', self.id, nint)
        for attr in ('title', 'locale', 'perex', 'body'):
            setattr(self, attr, form.getfirst(attr, '', uni))
        self.uri = Article.make_uri(self.title)
        # if article is public, that is not draft
        self.public = form.getfirst('public', 0, int)
        self.format = form.getfirst('format', FORMAT_HTML, int)
        self.state = 2 if self.public else form.getfirst('state', 1, int)
        self.data = {}
        if author_id:
            self.author_id = author_id
    # enddef

    def append_tag(self, req, tag_id):
        m = driver(req)
        return m.append_tag(self, req, tag_id)

    def remove_tag(self, req, tag_id):
        m = driver(req)
        return m.remove_tag(self, req, tag_id)

    @staticmethod
    def tags(req, id):
        m = driver(req)
        return m.tags_list(req, id)

    @staticmethod
    def list(req, pager, perex=False, **kwargs):
        if pager.order not in ('create_date', 'public_date', 'title',
                               'locale'):
            pager.order = 'create_date'

        m = driver(req)
        return m.item_list(req, pager, perex, **kwargs)

    @staticmethod
    def make_uri(title):
        if not isinstance(title, unicode):
            title = uni(title)
        title = unidecode(title.lower())
        return sub('\W+', '_', title).strip('_')

    @staticmethod
    def test(req):
        m = driver(req)
        return m.test(req)
# endclass
