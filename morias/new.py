
from poorwsgi import *
from falias.sql import Sql
from falias.util import uni

from core.login import check_login, check_referer, rights
from core.render import generate_page
from core.errors import ACCESS_DENIED, NOT_FOUND
from core.lang import get_lang

from lib.menu import Item
from lib.pager import Pager
from lib.new import New

from admin import *

_check_conf = (
    # morias common block
    ('morias', 'db', Sql, None),
)

rights += ['new_list', 'new_create', 'new_edit', 'new_delete']

admin_menu.append(Item('/admin/new', label="News", rights = ['new_list']))

@app.route("/test/new/db")
def test_db(req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT strftime('%%s','2013-12-09 18:19')*1")
    value = c.fetchone()[0]
    tran.commit()

    req.content_type = "text/plain; charset=utf-8"
    if value == 1386613140:
        return "Test of DB time Ok\n%s == %s" % (value, 1386613140)
    else:
        return "Test of DB time failed\n%s != %s" % (value, 1386613140)
#enddef

@app.route('/admin/new')
def admin_new(req):
    check_login(req, '/login?referer=/admin/new')
    check_right(req, 'new_list')

    error = req.args.getfirst('error', 0, int)

    pager = Pager(sort = 'desc')
    pager.bind(req.args)

    rows = New.list(req, pager)
    return generate_page(req, "admin/new.html",
                        menu = correct_menu(req, admin_menu),
                        pager = pager, rows = rows, error = error)
#enddef

@app.route('/admin/new/add', method = state.METHOD_GET_POST)
def admin_new_add(req):
    check_login(req, '/login?referer=/admin/new/add')
    check_right(req, 'new_create', '/admin/new?error=%d' % ACCESS_DENIED)

    if req.method == 'POST':
        new = New()
        new.bind(req.form)
        error = new.add(req)

        if error:
            return generate_page(req, "admin/new_mod.html",
                        menu = correct_menu(req, admin_menu),
                        new = new, error = error)

        #redirect(req, '/admin/new/mod?new_id=%d' % new.id)
        redirect(req, '/admin/new')
    #end

    return generate_page(req, "admin/new_mod.html",
                        menu = correct_menu(req, admin_menu))
#enddef

@app.route('/admin/new/mod', state.METHOD_GET_POST)
def admin_new_mod(req):
    check_login(req, '/login?referer=/admin/new/mod')
    check_right(req, 'new_edit', '/admin/new?error=%d' % ACCESS_DENIED)

    new = New(req.args.getfirst('new_id', 0, int))
    
    if req.method == 'POST':
        new.bind(req.form)
        error = new.mod(req)
        if error:
            return generate_page(req, "admin/new_mod.html",
                                    menu = correct_menu(req, admin_menu),
                                    new = new, error = error)
        #endif
        redirect(req, '/admin/new')
    #end
    error = new.get(req)
    if error: redirect(req, '/admin/new?error=%d' % NOT_FOUND)
    return generate_page(req, "admin/new_mod.html",
                        menu = correct_menu(req, admin_menu),
                        new = new)
#enddef

@app.route('/admin/new/disable')
@app.route('/admin/new/enable')
def admin_new_enable(req):
    check_login(req, '/login?referer=/admin/new')
    check_right(req, 'new_delete', '/admin/new?error=%d' % ACCESS_DENIED)
    check_referer(req, '/admin/new')
    
    new = New(req.args.getfirst('new_id', 0, int))
    new.enabled = int(req.uri == '/admin/new/enable')
    new.enable(req)
    redirect(req, '/admin/new')
#enddef

@app.route('/new/list')
def new_list(req):
    error = req.args.getfirst('error', 0, int)
    locale = req.args.getfirst('locale', get_lang(req), uni)

    pager = Pager(limit = 5, sort = 'desc', order = 'create_date')
    pager.bind(req.args)

    if 'locale' in req.args:                    # if locale is explicit set
        pager.set_params(locale = locale)

    rows = New.list(req, pager, body = True, enabled = 1, locale = (locale, ''))
    return generate_page(req, "new_list.html",
                        pager = pager, rows = rows, error = error, lang = locale)
#enddef

@app.route('/new/detail')
def new_detail(req):
    new = New(req.args.getfirst('new_id', 0, int))

    error = new.get(req)
    if error: redirect(req, '/new/list?error=%d' % NOT_FOUND)
    return generate_page(req, "new_detail.html",
                        new = new)
#enddef

