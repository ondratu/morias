from poorwsgi import app, redirect

from lib.menu import Menu

from admin import admin_menu

eshop_menu = Menu('eShop')
admin_menu.append(eshop_menu)


@app.route('/admin/eshop')
def admin_menu(req):
    redirect(req, '/admin#eShop')   # redirect to eShop section on admin page
