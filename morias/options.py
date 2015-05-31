from poorwsgi import *
from falias.sql import Sql
from falias.util import uniq, nuni, uni

import json

from core.render import generate_page
from core.login import check_login, check_right

from lib.menu import Item
from lib.pager import Pager
from lib.options import Option, check_timestamp, load_options

from admin import system_menu

_check_conf = (
    # morias common block
    ('morias', 'db', Sql),
    ('options', 'timestamp', unicode, 'tmp/options.timestamp'),
)

module_right = 'admin'

system_menu.append(Item('/admin/system/options', label="Options",
                        symbol="options", rights = [module_right]))


timestamp = -1

@app.pre_process()
def check_options(req):
    global timestamp

    check = check_timestamp(req)
    if check > timestamp:       # if last load was in past to timestamp file
        req.log_error("file timestamp is older, loading options from DB...",
                        state.LOG_INFO)
        load_options(req)
        timestamp = check
#emddef

@app.route('/admin/system/options')
def admin_options(req):
    check_login(req)
    check_right(req, module_right)

    section = req.args.getfirst('section', '', uni)
    module = req.args.getfirst('module', '', uni)
    kwargs = {}
    if section != 'all':
        kwargs['section'] = section
    if module != 'all':
        kwargs['module'] = module

    pager = Pager()
    pager.bind(req.args)
    options = Option.list(req, pager, **kwargs)

    return generate_page(req, "admin/options.html", pager = pager,
                        options = options, sections = Option.sections_list(req),
                        modules = Option.modules_list(req), section = section,
                        module = module)
#enddef

@app.route('/admin/system/options/<session:word>/<option:re:[\w-]+>',
            method = state.METHOD_PUT)
def admin_options_edit(req, section, option):
    check_login(req)
    check_right(req, module_right)

    if section == 'morias' and option == 'debug':
        req.status = state.HTTP_BAD_REQUEST
        req.content_type = 'application/json'
        return json.dumps({'reason': 'denied_option'})

    value = req.form.getfirst('value', None, nuni)
    if value is None:
        req.status = state.HTTP_BAD_REQUEST
        req.content_type = 'application/json'
        return json.dumps({'reason': 'value_is_none'})

    item = Option(section, option)
    item.value = value
    error = item.set(req)
    if error != item:
        req.status = state.HTTP_BAD_REQUEST
        req.content_type = 'application/json'
        return json.dumps({'reason': option_errors[error]})

    req.content_type = 'application/json'
    return json.dumps({'value': value})
#enddef
