from poorwsgi import *

from lib.menu import Menu

from admin import admin_menu

eshop_menu = Menu('eShop')
admin_menu.append(eshop_menu)

@app.route('/admin/eshop')
def admin_menu(req):
    # default admin module is store
    redirect(req, '/admin#eShop')
