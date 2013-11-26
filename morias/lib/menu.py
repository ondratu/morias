
class Item(object):
    def __init__(self, uri, label = None, title = None, rights = []):
        self.uri = uri
        self.label = label
        self.title = title
        self.rights = rights

    def __re_pr__(self):
        return super(Item, self).__repr__() + ": " + self.__dict__.__repr__()
