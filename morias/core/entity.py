
from json import dumps, loads

class Entity(object):

    def __init__(self, id, dump = []):
        self.id = id
        self._dump = dump
    #enddef

    def loads(self, json):
        data = loads(json)
        for key, val in data.items():
            self.__setattr__(key,val)
    #enddef

    def dumps(self):
        tojson = {}
        for k,v in self.__dict__.items():
            if k in self._dump:
                tojson[k] = v

        return dumps(tojson)
    #enddef

    def toTeng(self, dataRoot):
        dataRoot.addVariable('id', self.id)
    #enddef
#endclass
