from poorwsgi import *
from falias.sql import Sql
from falias.util import Object

from core.render import generate_page
from core.login import rights, do_login, do_logout, check_login, check_referer

from lib.menu import Item, correct_menu
from lib.pager import Pager
from lib.login import Login

from admin import *
from user import *
from core.errors import *

_check_conf = (
    ('morias', 'salt', unicode, None),              # salt for passwords
    ('morias', 'db', Sql, None),                    # database configuration
    ('morias', 'register', bool, False),            # if users can regiser
)

rights += ['login_list', 'login_create', 'login_ban']

admin_menu.append(Item('/admin/logins', label="Logins", rights = ['login_list']))
user_menu.append(Item('/user/profile', label="Profile", rights = ['user']))

@app.route("/test/logins/db")
def test_db(req):
    data = (None, 123, 3.14, "user@domain.xy", "'; SELECT 1; SELECT")
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

@app.route('/login', method = state.METHOD_GET_POST)
def login(req):
    referer = req.args.getfirst('referer', '', str)

    data = Object()
    data.referer = referer
    data.email = ''

    if req.method == 'POST':
        login = Login()
        ip = 'ip' in req.form
        login.bind(req.form, req.cfg.morias_salt)
        if login.find(req):
            do_login(req, login.simple(), ip)
            if referer:
                redirect(req, referer)
            if 'admin' in login.rights or 'super' in login.rights:
                redirect(req, '/admin')
            if 'user' in login.rights:
                redirect(req, '/user')
            redirect(req, '/')

        data.ip = ip
        data.email = login.email
        data.error = BAD_LOGIN

    return generate_page(req, "login.html", data = data)
#enddef

@app.route('/logout')
def logout(req):
    do_logout(req)
    redirect(req, req.referer or '/')
#enddef

@app.route('/admin/logins')
def admin_logins(req):
    check_login(req)
    check_right(req, 'login_list')

    error = req.args.getfirst('error', 0, int)

    pager = Pager()
    pager.bind(req.args)

    rows = Login.list(req, pager)
    return generate_page(req, "admin/logins.html",
                        menu = correct_menu(req, admin_menu),
                        pager = pager, rows = rows, error = error)
#enddef

@app.route('/admin/logins/add', method = state.METHOD_GET_POST)
def admin_logins_add(req):
    check_login(req)
    check_right(req, 'login_create', '/admin/logins?error=%d' % ACCESS_DENIED)

    if req.method == 'POST':
        login = Login()
        login.bind(req.form, req.cfg.morias_salt)
        error = login.add(req)

        if error:
            return generate_page(req, "admin/logins_mod.html",
                            menu = correct_menu(req, admin_menu),
                            rights = rights,
                            item = login, error = error)

        redirect(req, '/admin/logins/%d' % login.id)
    #end

    return generate_page(req, "admin/logins_mod.html",
                            menu = correct_menu(req, admin_menu),
                            rights = rights)
#enddef

@app.route('/admin/logins/<id:int>', state.METHOD_GET_POST)
def admin_logins_mod(req, id):
    check_login(req)
    check_right(req, 'login_create', '/admin/logins?error=%d' % ACCESS_DENIED)

    login = Login(id)

    state = None
    if req.method == 'POST':
        login.bind(req.form, req.cfg.morias_salt)
        state = login.mod(req)

        if state < 100:
            return generate_page(req, "admin/logins_mod.html",
                                 menu = correct_menu(req, admin_menu),
                                 rights = rights,
                                 item = login, error = state)
        #endif
    #endif

    if not login.get(req):
        redirect(req, '/admin/logins?error=%d' % NOT_FOUND)
    return generate_page(req, "admin/logins_mod.html",
                            menu = correct_menu(req, admin_menu),
                            rights = rights,
                            item = login, state = state)
#enddef

@app.route('/admin/logins/<id:int>/disable', state.METHOD_POST)
@app.route('/admin/logins/<id:int>/enable', state.METHOD_POST)
def admin_logins_enable(req, id):
    check_login(req, '/login?referer=/admin/logins')
    check_right(req, 'login_ban', '/admin/logins?error=%d' % ACCESS_DENIED)
    check_referer(req, '/admin/logins')

    login = Login(id)
    if req.login.id == login.id:
        redirect(req, '/admin/logins?error=%d' % ACCESS_DENIED)

    login.enabled = int(req.uri.endswith('/enable'))
    login.enable(req)
    redirect(req, '/admin/logins')
#enddef

@app.route('/user/profile', state.METHOD_GET_POST)
def user_logins_pref(req):
    check_login(req)

    login = Login(req.login.id)

    state = None
    if req.method == 'POST':
        login.bind(req.form, req.cfg.morias_salt)
        state = login.pref(req)

        if state < 100:
            return generate_page(req, "user/login_pref.html",
                                 menu = correct_menu(req, user_menu),
                                 error = state)
        #endif
    #endif

    login.get(req)
    req.login = login
    return generate_page(req, "user/login_pref.html",
                        menu = correct_menu(req, user_menu),
                        state = state)
#enddef
