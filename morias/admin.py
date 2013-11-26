
from poorwsgi import *
from core.login import check_login, check_right

admin_menu = []

@app.route('/admin')
def root(req):
    check_login(req, '/login?referer=/admin')
    check_right(req, 'admin')
    if len(admin_menu) == 1:    # if there is only one admin page, redirect
        redirect(req, admin_menu[0].uri)
    return generate_page(req, "admin.html", menu = admin_menu)
