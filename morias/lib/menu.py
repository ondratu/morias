from morias.core.login import do_match_right


class Item(object):
    def __init__(self, uri, label=None, title=None, rights=[],
                 symbol=None, locale='', role=None):
        self.uri = uri
        self.label = label
        self.title = title
        self.rights = rights
        self.symbol = symbol
        self.locale = locale
        self.role = role

    def __repr__(self):
        return str(self.__dict__)


class Menu(object):
    def __init__(self, label, symbol=None, locale='', role=None):
        self.label = label
        self.symbol = symbol
        self.locale = locale
        self.role = role
        self.items = []

    def append(self, item):
        if isitem(item) or ismenu(item):
            self.items.append(item)

    def extend(self, menu):
        for item in menu:
            self.items.append(item)

    def __iter__(self):
        return iter(self.items)

    def __getitem__(self, i):
        return self.items[i]

    def __len__(self):
        return len(self.items)

    def __rep_r__(self):
        return str(self.__dict__)

    @staticmethod
    def base(menu):
        return Menu(menu.label,
                    menu.symbol,
                    menu.locale,
                    menu.role)


def isitem(obj):
    return isinstance(obj, Item)


def ismenu(obj):
    return isinstance(obj, Menu)


def correct_menu(req, menu, retval=None):
    new_menu = retval if ismenu(retval) else Menu.base(menu)
    for item in menu:
        if isitem(item) and do_match_right(req, item.rights):
            new_menu.append(item)
        elif ismenu(item):
            submenu = correct_menu(req, item)
            if len(submenu) > 0:
                new_menu.append(submenu)
    return new_menu
