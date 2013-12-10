
from poorwsgi import *

from core.login import check_login, check_right, match_right
from core.render import generate_page

from lib.menu import correct_menu

admin_menu = []

@app.route('/admin')
def root(req):
    check_login(req, '/login?referer=/admin')
    check_right(req, 'admin')

    menu = correct_menu(req, admin_menu)

    if len(menu) > 0:    # if there is only one admin page, redirect
        redirect(req, menu[0].uri)
    return generate_page(req, "admin/admin.html", menu = menu)
