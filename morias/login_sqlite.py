from poorwsgi import *
from falias.sql import Sql

import json

from core.render import Object, generate_page
from lib.login import Login

import core.login, core.errors

_check_conf = (
    ('morias', 'salt', str, None),
    ('morias', 'db', Sql, None)
)


def Login_find(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT login_id, rights FROM login "
                "WHERE email = %s AND passwd = %s AND enabled = 1",
                (self.email, self.passwd))
    row = c.fetchone()
    tran.commit()

    if not row: return False
    self.id = row[0]
    self.rights = json.loads(row[1])
    return True
Login.find = Login_find


@app.route('/login', method = state.METHOD_GET_POST)
def login(req):
    form = FieldStorage(req)
    referer = form.getfirst('referer', '', str)
    
    data = Object()
    data.referer = referer
    data.email = ''

    if req.method == 'POST':
        login = Login()
        ip = 'ip' in form
        login.bind(form, req.cfg.morias_salt)
        if login.find(req):
            core.login.do_login(req, login, ip)
            if referer:
                redirect(req, referer)
            if 'admin' in login.rights:
                redirect(req, '/admin')
            if 'user' in login.rights:
                redirect(req, '/user')
            redirect(req, '/')

        data.ip = ip
        data.email = login.email
        data.error = core.errors.BAD_LOGIN

    return generate_page(req, "login.html", data = data)
#enddef

@app.route('/logout')
def logout(req):
    core.login.do_logout(req)
    redirect(req, req.referer or '/')
#enddef
