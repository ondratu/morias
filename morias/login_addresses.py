# This module can edit additional client info for logins like addresse,
# phone number, etc

from poorwsgi import *

import json

from core.login import check_login, check_right
from core.render import generate_page

from lib.menu import Item
from lib.login import Login
from lib.login_addresses import Addresses

from user import user_info_menu
from login import module_right
from admin import system_menu

_check_conf = (
    ('login_addresses', 'region', bool, False),
    ('login_addresses', 'country', bool, False),
)

user_info_menu.append(Item('/user/addresses', label="Addresses", symbol="address",
                    rights = ['user']))

@app.route('/admin/logins/<id:int>/addresses',
        method = state.METHOD_GET | state.METHOD_PUT)
def admin_login_addresses(req, id):
    check_login(req)
    check_right(req, module_right)

    login = Login(id)

    if req.method == 'GET':
        if not login.get(req):
            raise SERVER_RETURN(state.HTTP_NOT_FOUND)

        return generate_page(req, "admin/logins_addresses.html",
                            item = login,
                            cfg_region = req.cfg.login_addresses_region,
                            cfg_country = req.cfg.login_addresses_country)

    # req.method == 'PUT'       # ajax put
    addresses = Addresses.bind(req.json)
    if not addresses.mod(req, id) is None:
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    login.get(req)
    req.content_type = 'application/json'
    return json.dumps(login.data.get('addresses', {}))
#enddef

@app.route('/user/addresses',
        method = state.METHOD_GET | state.METHOD_PUT)
def user_addresses(req):
    check_login(req)

    if req.method == 'GET':
        return generate_page(req, "user/addresses.html",
                            cfg_region = req.cfg.login_addresses_region,
                            cfg_country = req.cfg.login_addresses_country)

    # req.method == 'PUT'       # ajax put
    addresses = Addresses.bind(req.json)
    addresses.mod(req, req.login.id)

    req.login.get(req)
    req.content_type = 'application/json'
    return json.dumps(req.login.data.get('addresses', {}))
#enddef
