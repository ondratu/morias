from core.login import do_match_right

class Item(object):
    def __init__(self, uri, label = None, title = None, rights = []):
        self.uri = uri
        self.label = label
        self.title = title
        self.rights = rights

def correct_menu(req, menu):
    return list ( item for item in menu if do_match_right(req, item.rights) )
