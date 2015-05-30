
from falias.util import uni
from hashlib import md5

import json

from lib.tree import Item

from lib import menu

class MenuItem(Item):
    """ MenuItem from sql have this structure:

        #!python
        { 'item_id' : int,
          'parent'  : int or None,
          'next'    : int or None,
          'order'   : int or None,
          'title'   : str,
          'link'    : str,
          'locale'  : str,
          'state'   : 0 | 1
        }
    """

    ID      = 'item_id'
    ORDER   = 'ordering'
    TABLE   = 'page_menu'

    def get(self, req):
        row = super(MenuItem, self).get(req)
        if not row:
            return row
        self.title  = row['title']
        self.link   = row['link']
        self.locale = row['locale']
        self.state  = row['state']
        return self
    #enddef

    def add(self, req):
        return super(MenuItem, self).add(req, title = self.title,
                link = self.link, locale = self.locale, state = 1)

    def mod(self, req):
        return super(MenuItem, self).mod(req, title = self.title,
                link = self.link, locale = self.locale)

    def enabled(self, req, enabled = True):
        self.state = int(enabled)
        return super(MenuItem.self).mod(req, state = state)

    def bind(self, form):
        super(MenuItem, self).bind(form)
        self.title  = form.getfirst('title', '', uni)
        self.link   = form.getfirst('link', '', uni)
        self.locale = form.getfirst('locale', '', uni)

    @staticmethod
    def list(req, pager, **kwargs):
        if pager.order not in (MenuItem.ID, MenuItem.PARENT, MenuItem.ORDER, 'title', 'locale'):
            pager.order = MenuItem.ORDER

        if pager.limit == -1 and pager.order == MenuItem.ORDER:
            rows = Item.full_tree(req, MenuItem, **kwargs)
        else:
            rows = Item.list(req, MenuItem, pager, **kwargs)

        items = []
        for row in rows:
            item = MenuItem(row[MenuItem.ID])
            item.parent = row[MenuItem.PARENT]
            item.next   = row[MenuItem.NEXT]
            item.order  = row[MenuItem.ORDER]
            item.title  = row['title']
            item.link   = row['link']
            item.state  = row['state']
            item.locale = row['locale']
            item.level  = row['_level'] if '_level' in row else 0
            item.md5    = md5(json.dumps(item.__dict__)).hexdigest()
            items.append(item)
        return items


    @staticmethod
    def get_menu(req):
        rows =  Item.full_tree(req, MenuItem)
        items = { None: menu.Menu('') }
        for row in rows:
            if row[MenuItem.PARENT]:
                items[row[MenuItem.PARENT]] = menu.Menu('')

        for row in rows:
            if row['state'] == 0:
                continue            # only active items
            item = items.get(row[MenuItem.ID], menu.Item(row['link']))
            item.label = row['title']
            item.locale = row['locale']

            items[row[MenuItem.PARENT]].append(item)

        return items[None]
    #enddef
#endclass
