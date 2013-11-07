class Login(object):
    def __init__(self):
        self.ip = True
        self.referer = ''
        self.email = ''
        self.passwd = ''
        super(Login, self).__init__()
    #enddef

    def bind(self, form):
        self.ip = form.get('ip', '', str)
        self.referer = form.get('referer', '', str)
        self.user = form.get('user', '', str)
        self.passwd = form.get('passwd', '', str)
    #enddef
