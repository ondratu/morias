"""Module for generic codebooks.

Cotains method for:
    * administrations
    * value suggesting
"""
from poorwsgi import app, state
from falias.sql import Sql
from falias.util import nuni

import json

from core.login import rights, check_login, check_right, create_token, \
    check_token
from core.render import generate_page

from lib.menu import Item as MenuItem
from lib.pager import Pager
from lib.codebook import Item

from admin import codebooks_menu

_check_conf = (
    # morias common block
    ('morias', 'db', Sql, None),
)

module_right = 'codebooks'
rights.add(module_right)
codebooks = {}


def _call_conf(cfg, parser):
    for option in parser.options('codebooks'):
        codebooks[option] = parser.get('codebooks', option, cls=tuple)
        codebooks_menu.append(MenuItem('/admin/codebooks/%s' % option,
                                       label=codebooks[option][0],
                                       symbol=option, rights=[module_right]))


def build_class(codebook):
    class Codebook(Item):
        LABEL, TABLE, ID, VALUE = codebooks[codebook]
    return Codebook


@app.route('/admin/codebooks/<codebook:word>')
def admin_codebook_view(req, codebook):
    check_login(req)
    check_right(req, module_right)

    Codebook = build_class(codebook)
    search = req.args.getfirst('search', fce=nuni)

    pager = Pager(order='value')
    pager.bind(req.args)

    if search:
        pager.set_params(search=search)

    items = Codebook.list(req, Codebook, pager, search=search)

    return generate_page(req, "admin/codebook.html",
                         token=create_token(req), codebook=codebook,
                         pager=pager, items=items, search=search)
# enddef


def json_response(req, data={}):
    req.content_type = 'application/json'
    return json.dumps(data)


@app.route('/admin/codebooks/<codebook:word>/<id:int>',
           method=state.METHOD_PUT)
@app.route('/admin/codebooks/<codebook:word>/add', method=state.METHOD_POST)
def admin_codebook_add_update(req, codebook, id=None):
    check_login(req)
    check_right(req, module_right)
    check_token(req, req.form.get('token'),
                uri='/admin/codebooks/%s' % codebook)

    Codebook = build_class(codebook)

    item = Codebook(id)
    item.bind(req.form)
    if not item.value:
        req.status = state.HTTP_BAD_REQUEST
        return json_response(req, {'reason': 'empty_value'})

    if (item.mod(req) if id else item.add(req)):
        return json_response(req)

    req.status = state.HTTP_BAD_REQUEST
    return json_response(req, {'reason': 'value_exist'})
# enddef


@app.route('/admin/codebooks/<codebook:word>/<id:int>',
           method=state.METHOD_DELETE)
def admin_menu_delete(req, codebook, id):
    check_login(req)
    check_right(req, module_right)
    check_token(req, req.args.get('token'),
                uri='/admin/codebooks/%s' % codebook)

    Codebook = build_class(codebook)

    item = Codebook(id)
    if item.delete(req):
        return json_response(req)

    req.status = state.HTTP_BAD_REQUEST
    req.content_type = 'application/json'
    return json_response(req, {'reason': 'integrity_error'})
# enddef
