from poorwsgi import *
from falias.sql import Sql

from core.render import Object, generate_page
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

rights += ['login_list', 'login_create', 'login_edit', 'login_ban']

admin_menu.append(Item('/admin/login', label="Logins", rights = ['login_list']))
user_menu.append(Item('/user/profile', label="Profile", rights = ['user']))

@app.route("/test/login/db")
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

@app.route('/admin/login')
def admin_login(req):
    check_login(req, '/login?referer=/admin/login')
    check_right(req, 'login_list')

    form = FieldStorage(req)
    error = form.getfirst('error', 0, int)

    pager = Pager()
    pager.bind(form)

    rows = Login.list(req, pager)
    return generate_page(req, "admin/login.html",
                        menu = correct_menu(req, admin_menu),
                        pager = pager, rows = rows, error = error)
#enddef

@app.route('/admin/login/add', method = state.METHOD_GET_POST)
def admin_login_add(req):
    check_login(req, '/login?referer=/admin/login/add')
    check_right(req, 'login_create', '/admin/login?error=%d' % ACCESS_DENIED)

    if req.method == 'POST':
        form = FieldStorage(req)
        login = Login()
        login.bind(form, req.cfg.morias_salt)
        error = login.add(req)

        if error:
            return generate_page(req, "admin/login_mod.html",
                            menu = correct_menu(req, admin_menu),
                            rights = rights,
                            item = login, error = error)

        #redirect(req, '/admin/login/mod?login_id=%d' % login.id)
        redirect(req, '/admin/login')
    #end

    return generate_page(req, "admin/login_mod.html",
                            menu = correct_menu(req, admin_menu),
                            rights = rights)
#enddef

@app.route('/admin/login/mod', state.METHOD_GET_POST)
def admin_login_mod(req):
    check_login(req, '/login?referer=/admin/login/mod')
    check_right(req, 'login_edit', '/admin/login?error=%d' % ACCESS_DENIED)

    form = FieldStorage(req)
    login = Login(form.getfirst('login_id', 0, int))
    if req.login.id == login.id:
        redirect(req, '/admin/login?error=%d' % ACCESS_DENIED)

    state = None
    if req.method == 'POST':
        login.bind(form, req.cfg.morias_salt)
        state = login.mod(req)

        if state < 100:
            return generate_page(req, "admin/login_mod.html",
                                 menu = correct_menu(req, admin_menu),
                                 rights = rights,
                                 item = login, error = state)
        #endif
    #endif

    if not login.get(req):
        redirect(req, '/admin/login?error=%d' % NOT_FOUND)
    return generate_page(req, "admin/login_mod.html",
                            menu = correct_menu(req, admin_menu),
                            rights = rights,
                            item = login, state = state)
#enddef

@app.route('/admin/login/disable')
@app.route('/admin/login/enable')
def admin_login_enable(req):
    check_login(req, '/login?referer=/admin/login')
    check_right(req, 'login_ban', '/admin/login?error=%d' % ACCESS_DENIED)
    check_referer(req, '/admin/login')

    form = FieldStorage(req)
    login = Login(form.getfirst('login_id', 0, int))
    if req.login.id == login.id:
        redirect(req, '/admin/login?error=%d' % ACCESS_DENIED)

    login.enabled = int(req.uri == '/admin/login/enable')
    login.enable(req)
    redirect(req, '/admin/login')
#enddef

@app.route('/user/profile', state.METHOD_GET_POST)
def user_login_pref(req):
    check_login(req, '/login?referer=/user/profile')

    form = FieldStorage(req)
    login = Login(req.login.id)

    state = None
    if req.method == 'POST':
        login.bind(form, req.cfg.morias_salt)
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
