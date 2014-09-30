
from poorwsgi import *
from falias.sql import Sql
from falias.util import uni, nint

from core.login import check_login, check_referer, match_right, rights, \
        do_check_right
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

module_rights = ('news_editor', 'news_author')
rights.update(module_rights)

content_menu.append(Item('/admin/news', label="News", rights = module_rights))

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
    match_right(req, module_rights)

    show = req.args.getfirst('show', '', uni)

    pager = Pager(sort = 'desc')
    pager.bind(req.args)

    kwargs = {}

    if show == 'ready':
        pager.set_params(show = show)
        kwargs['state'] = 2
        kwargs['public_date'] = 0
    elif show == 'drafts':
        pager.set_params(show = show)
        kwargs['state'] = 1
    else:
        show = None

    if not do_check_right(req, 'news_editor'):
        kwargs['author_id'] = req.login.id

    rows = New.list(req, pager, **kwargs)
    return generate_page(req, "admin/news.html",
                        pager = pager, rows = rows, show = show)
#enddef

@app.route('/admin/news/add', method = state.METHOD_GET_POST)
def admin_news_add(req):
    check_login(req)
    match_right(req, module_rights)

    new = New()
    if req.method == 'POST':
        new.bind(req.form, req.login.id)
        error = new.add(req)

        if error:
            return generate_page(req, "admin/news_mod.html",
                        new = new, error = error)

        redirect(req, '/admin/news/%d' % new.id)
    #end

    new.state = 2 if do_check_right(req, 'news_editor') else 1
    return generate_page(req, "admin/news_mod.html", new = new)
#enddef

@app.route('/admin/news/<id:int>', state.METHOD_GET_POST)
def admin_news_mod(req, id):
    check_login(req)
    match_right(req, module_rights)

    new = New(id)
    if not new.get(req):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)
    if (not do_check_right(req, 'news_editor') and new.author_id != req.login.id):
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)

    if req.method == 'POST':
        new.bind(req.form)
        new.mod(req)

        if not new.get(req):
            raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    return generate_page(req, "admin/news_mod.html", new = new)
#enddef

@app.route('/admin/news/<id:int>/disable', state.METHOD_POST)
@app.route('/admin/news/<id:int>/enable', state.METHOD_POST)
def admin_news_enable(req, id):
    check_login(req, '/login?referer=/admin/news')
    match_right(req, module_rights)
    check_referer(req, '/admin/news')

    new = New(id)
    if not new.get(req):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    if (not do_check_right(req, 'news_editor')) and \
        (not (new.author_id == req.login.id and new.public_date.year == 1970)):
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)

    state = int(req.uri.endswith('/enable'))
    state = (state * 2) if new.public_date.year > 1970 else state
    new.set_state(req, state)

    redirect(req, '/admin/news')
#enddef

@app.route('/news/<id:int>')
def news_detail(req, id):
    new = New(id)

    if not new.get(req):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    return generate_page(req, "news_detail.html",
                        new = new,
                        staticmenu = req.cfg.get_static_menu(req) )
#enddef

@app.route('/news/<locale:word>/<id:int>')
def news_detail(req, locale, id):
    new = New(id)

    if not new.get(req):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    return generate_page(req, "news_detail.html",
                        new = new, locale = locale,
                        staticmenu = req.cfg.get_static_menu(req) )
#enddef

@app.route('/news')
@app.route('/news/<locale:word>')
def news_list(req, locale = None):
    locale = locale if locale else get_lang(req)

    pager = Pager(limit = 5, sort = 'desc', order = 'create_date')
    pager.bind(req.args)

    rows = New.list(req, pager, body = True, public = 1, locale = (locale, ''))
    return generate_page(req, "news_list.html",
                        pager = pager, rows = rows, lang = locale,
                        staticmenu = req.cfg.get_static_menu(req) )
#enddef
