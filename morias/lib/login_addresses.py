from falias.util import islistable, uni

from login import Login

address_items = ('type', 'name', 'address1', 'address2', 'city', 'region',
                 'zip','country')

class Addresses(object):
    def __init__(self):
        self.items = list()

    def mod(self, req, id):
        login = Login(id)
        return login._mod(req, ['data'], [{'addresses': self.items}])

    @staticmethod
    def address(struct):
        if not isinstance(struct, dict):
            return {}

        addr = {}
        for key in address_items:
            val = struct.get(key, '')
            if val != '': addr[key] = val

        return addr
    #enddef

    @staticmethod
    def bind(json):
        a = Addresses()
        addresses = json.get('addresses', [])
        if not islistable(addresses):
            return a

        for it in addresses:
            i = Addresses.address(it)
            if i: a.items.append(i)     # protect to empty addresses

        return a
    #enddef
