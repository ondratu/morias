
from poorwsgi import *

from core.login import check_login, check_right
from core.render import generate_page

from lib.menu import *
from user import user_menu

admin_sections = Menu('Administration')
admin_menu = admin_sections     # back compatibility

content_menu = Menu('Content')
codebooks_menu = Menu('Codebooks')
system_menu = Menu('System')

admin_menu.append(content_menu)
admin_menu.append(codebooks_menu)
admin_menu.append(system_menu)

@app.route('/admin')
def root(req):
    check_login(req)
    check_right(req, 'admin')

    no_section = Menu('')
    no_section.items = list(item for item in admin_sections if isitem(item))

    x_menu = Menu(admin_sections.label)
    x_menu.append(no_section)
    x_menu.items += [item for item in admin_sections if ismenu(item)]

    x_menu = correct_menu(req, x_menu)

    # if there is only one link, redirect to it
    if len(x_menu) == 1 and len(x_menu[0]) == 1:
        redirect(req, x_menu[0][0].uri)
    return generate_page(req, "admin/admin.html", admin_sections = x_menu)
