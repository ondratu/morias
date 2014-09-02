from poorwsgi import *

from core.login import check_login, do_check_login
from core.render import generate_page

from lib.menu import correct_menu, Menu

user_menu = Menu('User')  # menu for any users: Profile / Logout / Login / Register

@app.pre_process()
def append_menu(req):
    req.menu = user_menu

@app.route('/user')
def root(req):
    check_login(req)
    
    #if len(menu) > 0:
    #    redirect(req, menu[0].uri)
    return generate_page(req, "user.html")
