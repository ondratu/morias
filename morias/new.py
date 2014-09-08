
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

rights.update(('news_editor', 'news_author', 'news_redactor'))

content_menu.append(Item('/admin/news', label="News", rights = ['news_list']))

@app.route("/test/news/db")
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

@app.route('/admin/news')
def admin_news(req):
    check_login(req)
    check_right(req, 'news_editor')

    error = req.args.getfirst('error', 0, int)

    pager = Pager(sort = 'desc')
    pager.bind(req.args)

    rows = New.list(req, pager)
    return generate_page(req, "admin/news.html",
                        pager = pager, rows = rows, error = error)
#enddef

@app.route('/admin/news/add', method = state.METHOD_GET_POST)
def admin_news_add(req):
    check_login(req)
    check_right(req, 'news_editor', '/admin/news?error=%d' % ACCESS_DENIED)

    if req.method == 'POST':
        new = New()
        new.bind(req.form)
        error = new.add(req)

        if error:
            return generate_page(req, "admin/news_mod.html",
                        new = new, error = error)

        redirect(req, '/admin/news/%d' % new.id)
    #end

    return generate_page(req, "admin/news_mod.html")
#enddef

@app.route('/admin/news/<id:int>', state.METHOD_GET_POST)
def admin_news_mod(req, id):
    check_login(req)
    check_right(req, 'news_editor', '/admin/news?error=%d' % ACCESS_DENIED)

    new = New(id)

    if req.method == 'POST':
        new.bind(req.form)
        error = new.mod(req)
        if error:
            return generate_page(req, "admin/news_mod.html",
                                    new = new, error = error)

    error = new.get(req)
    if error: redirect(req, '/admin/news?error=%d' % NOT_FOUND)
    return generate_page(req, "admin/news_mod.html",
                        new = new)
#enddef

@app.route('/admin/news/<id:int>/disable', state.METHOD_POST)
@app.route('/admin/news/<id:int>/enable', state.METHOD_POST)
def admin_news_enable(req, id):
    check_login(req, '/login?referer=/admin/news')
    check_right(req, 'news_editor', '/admin/news?error=%d' % ACCESS_DENIED)
    check_referer(req, '/admin/news')

    new = New(id)
    new.enabled = int(req.uri.endswith('/enable'))
    new.enable(req)
    redirect(req, '/admin/news')
#enddef

@app.route('/news')
def news_list(req):
    error = req.args.getfirst('error', 0, int)
    locale = req.args.getfirst('locale', get_lang(req), uni)

    pager = Pager(limit = 5, sort = 'desc', order = 'create_date')
    pager.bind(req.args)

    if 'locale' in req.args:                    # if locale is explicit set
        pager.set_params(locale = locale)

    rows = New.list(req, pager, body = True, enabled = 1, locale = (locale, ''))
    return generate_page(req, "news_list.html",
                        pager = pager, rows = rows, error = error, lang = locale)
#enddef

@app.route('/news/<id:int>')
def news_detail(req, id):
    new = New(id)

    error = new.get(req)
    if error: redirect(req, '/news?error=%d' % NOT_FOUND)
    return generate_page(req, "news_detail.html",
                        new = new)
#enddef

