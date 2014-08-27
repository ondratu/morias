from poorwsgi import *

from core.login import check_login
from core.render import generate_page

from lib.menu import correct_menu

user_menu = []

@app.route('/user')
def root(req):
    check_login(req)
    
    menu = correct_menu(req, user_menu)
    
    if len(menu) > 0:
        redirect(req, menu[0].uri)
    return generate_page(req, "user.html", menu = menu)
