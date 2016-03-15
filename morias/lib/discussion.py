from falias.util import nint, uni

from json import dumps, loads
from time import time
from datetime import datetime

from morias.core.errors import ErrorValue
from wotree import WoItem


class EmptyTitle(ErrorValue):
    code = 1
    reason = 'empty_title'
    message = 'Empty title'


class EmptyAuthor(ErrorValue):
    code = 2
    reason = 'empty_author'
    message = 'Empty Author'


class EmptyBody(ErrorValue):
    code = 3
    reason = 'empty_body'
    message = 'Empty Body'


class Comment(WoItem):
    """Comment object have this structure:

    ..code: python

        {'id'           : string,
         'object_id'    : int,
         'author'       : string,
         'author_id'    : int,
         'create_date'  : int,
         'title'        : string,
         'body'         : string,
         'data'         : {}}
    """
    ID = 'comment_id'
    TABLE = 'discussion'
    OBJECT_ID = 'object_id'
    __attrs = ('author', 'author_id', 'create_date', 'title', 'body', 'data')

    def add(self, req, parent=''):
        if not self.title:
            return EmptyTitle(comment=self)
        if not self.author:
            return EmptyAuthor(comment=self)
        if not self.body:
            return EmptyBody(comment=self)

        self.create_date = int(time())
        kwargs = {self.OBJECT_ID: self.object_id,
                  'author': self.author,
                  'author_id': self.author_id,
                  'create_date': self.create_date,
                  'title': self.title,
                  'body': self.body,
                  'data': dumps(self.data)}
        return super(Comment, self).add(req, parent, **kwargs)

    def _last(self, req, c, parent):
        cond = {self.OBJECT_ID: self.object_id}
        return super(Comment, self)._last(req, c, parent, **cond)

    def get(self, req):
        cond = {self.OBJECT_ID: self.object_id}
        rv = super(Comment, self).get(req, **cond)
        if rv is None:
            return None
        for attr in self.__attrs:
            setattr(self, attr, rv[attr])
        self.data = loads(self.data)
        return self

    def mod(self, req):
        kwargs = {self.OBJECT_ID: self.object_id,
                  'author': self.author,
                  'author_id': self.author_id,
                  'title': self.title,
                  'body': self.body,
                  'data': dumps(self.data)}
        return super(Comment, self).mod(req, **kwargs)

    def bind(self, form, **kwargs):
        self.id = form.getfirst(self.ID, self.id, nint)
        self.object_id = form.getfirst(self.OBJECT_ID, fce=int)
        self.author = form.getfirst('author', '', uni)
        self.author_id = form.getfirst('author_id', None, nint)
        self.title = form.getfirst('title', '', uni)
        self.body = form.getfirst('body', '', uni)
        self.data = kwargs

    @staticmethod
    def list(req, cls, object_id, pager, **kwargs):
        if pager.order not in (cls.ID, 'title'):
            pager.order = cls.ID

        kwargs.update({cls.OBJECT_ID: object_id})
        rows = WoItem.list(req, cls, pager, **kwargs)

        items = []
        for row in rows:
            item = cls()
            for k, v in row.items():
                if k == 'create_date':
                    item.create_date = datetime.fromtimestamp(v)
                elif k == 'data':
                    item.data = loads(v)
                elif k == cls.ID:
                    item.id = v
                else:
                    setattr(item, k, v)
            items.append(item)
        return items
    # enddef
