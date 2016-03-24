from poorwsgi import app, state, redirect, send_json
from falias.sql import Sql
from falias.util import nuni, ObjectEncoder


from morias.core.login import rights, check_login, check_right, create_token, \
    check_token
from morias.core.render import generate_page
from morias.core.errors import ErrorValue

from morias.lib.menu import Item
from morias.lib.pager import Pager
from morias.lib.redirects import Redirect
from morias.lib.timestamp import check_timestamp

from admin import content_menu

_check_conf = (
    # morias common block
    ('morias', 'db', Sql, None),
    ('redirects', 'timestamp', unicode, 'tmp/redirects.timestamp'),
)


def _call_conf(cfg, parser):
    refresh_links(cfg, cfg.redirects_timestamp, False)

timestamp = -1
module_right = 'menu_modify'
rights.add(module_right)
content_menu.append(Item('/admin/redirects', label="Redirects",
                         symbol="redirects", rights=[module_right]))


@app.pre_process()
def load_redirects(req):
    if req.uri_rule in ('_debug_info_', '_send_file_', '_directory_index_'):
        return  # this methods no need this pre process
    refresh_links(req, req.cfg.redirects_timestamp)


def refresh_links(req, cfg_timestamp, clear=True):
    """ refresh redirect links from db if timestamp is change """
    global timestamp

    check = check_timestamp(req, cfg_timestamp)
    if check > timestamp:       # if last load was in past to timestamp file
        req.log_error("file timestamp is older, loading redirects from DB...",
                      state.LOG_INFO)

        if clear:
            for uri, hdls in app.handlers.items():
                if hdls.get(state.METHOD_GET) == redirect_uri:
                    app.pop_route(uri, state.METHOD_GET)
                    app.pop_route(uri, state.METHOD_HEAD)
        for it in Redirect.list(req, Pager(limit=-1), state=1):
            if it.src[-1] == '$':
                if not app.is_rroute(it.src):
                    req.cfg.log_info("Adding %s -> %s" % (it.src, it.dst))
                    app.set_rroute(it.src, redirect_ruri)
            else:
                if not app.is_route(it.src):
                    req.cfg.log_info("Adding %s -> %s" % (it.src, it.dst))
                    app.set_route(it.src, redirect_uri)

        timestamp = check
# enddef


def redirect_uri(req, *args):
    item = Redirect()
    item.src = req.uri
    item.get(req, key='src')
    redirect(req, item.dst,
             permanent=int(item.code == state.HTTP_MOVED_PERMANENTLY))


def redirect_ruri(req, *args):
    item = Redirect()
    item.src = req.uri_rule
    item.get(req, key='src')
    dst = item.dst.format(*args)
    print args
    redirect(req, dst,
             permanent=int(item.code == state.HTTP_MOVED_PERMANENTLY))


@app.route('/admin/redirects')
def admin_redirects(req):
    check_login(req)
    check_right(req, module_right)

    search = req.args.getfirst('search', fce=nuni)

    pager = Pager(order='value')
    pager.bind(req.args)

    if search:
        pager.set_params(search=search)

    items = Redirect.list(req, pager, search=search)

    return generate_page(req, "admin/redirects.html",
                         token=create_token(req),
                         pager=pager, items=items, search=search)
# enddef


@app.route('/admin/redirects/<id:int>', method=state.METHOD_PUT)
@app.route('/admin/redirects/add', method=state.METHOD_POST)
def admin_redirects_add_update(req, id=None):
    check_login(req)
    check_right(req, module_right)
    check_token(req, req.form.get('token'), uri='/admin/redirects')

    item = Redirect(id)
    item.bind(req.form)
    rv = item.mod(req) if id else item.add(req)

    if isinstance(rv, Redirect):
        return send_json(req, {})

    req.status = state.HTTP_BAD_REQUEST
    if isinstance(rv, ErrorValue):
        return send_json(req, rv, cls=ObjectEncoder)

    return send_json(req, {'reason': 'src_exist'})
# enddef


@app.route('/admin/redirects/<id:int>', method=state.METHOD_DELETE)
def admin_redirects_delete(req, id):
    check_login(req)
    check_right(req, module_right)
    check_token(req, req.args.get('token'), uri='/admin/redirects')

    item = Redirect(id)
    if not item.delete(req):
        req.status = state.HTTP_NOT_FOUND

    return send_json(req, {})
# enddef
