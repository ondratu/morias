from poorwsgi import *
from falias.sql import Sql

import core.login
from core.render import JData

_check_conf = (
    ('morias', 'salt', str, None),
    ('morias', 'db', Sql, None)
)

@app.route('/login')
def login(req):
    form = FieldStorage(req)
    data = JData()

    if req.method == 'POST':
        data.ip = True
        data.referer = form.get('referer', '', str)
        data.email = form.get('email', '', str)
        data.passwd = core.login(form.get('passwd', '', str), req.cfg.morias_salt)
        
    req.content_type = "text/plain; charset=utf-8"
    return str(form) + '\n' + str(form.keys()) + '\n' + \
        str(tuple( form[key] for key in form.keys() ))

