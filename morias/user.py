from poorwsgi import app, redirect

from core.login import check_login
from core.render import generate_page

from lib.menu import Menu, isitem, ismenu, correct_menu

# menu for any users: Profile / Logout / Login / Register
user_sections = Menu('User', role='user-menu')
user_menu = user_sections     # back compatibility

user_info_menu = Menu('Info')
user_sections.append(user_info_menu)


@app.pre_process()
def append_menu(req):
    req.menu = user_menu
    req.static_menu = Menu('Menu')      # static menu (from DB for example)


@app.route('/user')
def root(req):
    check_login(req)

    no_section = Menu('')
    no_section.items = list(item for item in user_sections if isitem(item))

    x_menu = Menu(user_sections.label)
    x_menu.append(no_section)
    x_menu.items += [item for item in user_sections if ismenu(item)]

    x_menu = correct_menu(req, x_menu)

    # if there is only one link, redirect to it
    if len(x_menu) == 1 and len(x_menu[0]) == 1:
        redirect(req, x_menu[0][0].uri)

    return generate_page(req, "user/user.html", user_sections=x_menu)
