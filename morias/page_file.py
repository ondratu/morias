# -*- coding: utf-8 -*-

from poorwsgi import *
from falias.sql import Sql

import core.login

_check_conf = (
    # morias common block
    ('morias', 'db', Sql, None),

    # pages block
    ('pages', 'source', str,  None), 
    ('pages', 'out',   str,  None),
)

core.login.rights += ['text_create', 'text_edit', 'text_delete']

@app.route("/page/test/db")
def test_db(req):
    data = (None, 123, 3.14, "úspěšný test", "'; SELECT 1; SELECT")
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT %s, %s, %s, %s, %s", data)
    copy = tuple(it.encode('utf-8') if isinstance(it, unicode) else it \
                        for it in c.fetchone())
    tran.commit()

    req.content_type = "text/plain; charset=utf-8"
    if copy == data:
        return "Test Ok\n" + str(data) + '\n' + str(copy)
    else:
        return "Test failed\n" + str(data) + '\n' + str(copy)
#enddef

@app.route('/')
def root(req):
    redirect(req, '/index.html', text="static index");

@app.route('/admin/page/edit', state.METHOD_GET_POST)
def admin_edit_page(req):
    pass
