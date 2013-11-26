
from core.login import sha1_sdigest

class Login(object):
    def __init__(self):
        self.id = None
        self.email = ''
        self.passwd = ''
        self.rights = []
        super(Login, self).__init__()
    #enddef

    def bind(self, form, salt):
        self.email = form.getfirst('email', '', str)
        self.passwd = sha1_sdigest(form.getfirst('passwd', '', str), salt)
    #enddef

    def find(self, req):
        raise RuntimeError('Method is not defined in login module!')
#endclass
