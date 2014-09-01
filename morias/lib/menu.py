from core.login import do_match_right
from inspect import stack
from sys import getrefcount

class Item(object):
    def __init__(self, uri, label = None, title = None, rights = [], symbol = None):
        self.uri = uri
        self.label = label
        self.title = title
        self.rights = rights
        self.symbol = symbol

    def __repr__(self):
        return str(self.__dict__)

#endclass Item

class Menu(object):
    def __init__(self, label, symbol = None):
        self.label = label
        self.symbol = symbol
        self.items = []

    def append(self, item):
        if isitem(item) or ismenu(item):
            self.items.append(item)

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __rep_r__(self):
        return str(self.__dict__)

#endclass Menu

def isitem(obj):
    return isinstance(obj, Item)

def ismenu(obj):
    return isinstance(obj, Menu)

def correct_menu(req, menu):
    new_menu = Menu(menu.label)
    for item in menu:
        if isitem(item) and do_match_right(req, item.rights):
            new_menu.append(item)
        elif ismenu(item):
            submenu = correct_menu(req, item)
            if len(submenu) > 0:
                new_menu.append(submenu)
    return new_menu
    #return list ( item for item in menu if ismenu(item) or do_match_right(req, item.rights) )
