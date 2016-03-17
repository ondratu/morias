from poorwsgi.request import Json


class Form(Json):
    def __init__(self, items):
        dict.__init__(self, items)
        self.getvalue = self.get
