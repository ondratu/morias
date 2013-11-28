
class Pager(object):
    def __init__(self, offset = 0, limit = 10, order = '', sort = 'asc'):
        self.offset = offset
        self.limit = limit
        self.order = order
        self.sort = sort
        self.total = 0
        super(Pager, self).__init__()
    #enddef

    def __re_pr__(self):
        return super(Pager, self).__repr__() + ": " + self.__dict__.__repr__()

    def bind(self, form):
        self.offset = form.getfirst("offset", self.offset, int)
        self.limit = form.getfirst("limit", self.limit, int)
        self.order = form.getfirst("order", self.order, str)
        
        sort = form.getfirst("sort", self.sort, str)
        self.sort = sort if sort in ('asc', 'desc') else self.sort

    def calculate(self):
        self.pages = (self.total -1) / self.limit
        self.page = self.offset / self.limit
#endclass
