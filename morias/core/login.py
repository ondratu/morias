# -*- coding: utf-8 -*-

from poorwsgi import state, redirect
from poorwsgi.session import PoorSession

from time import time
from hashlib import sha1

rights = ['admin', 'user', 'guest']

def do_login(req, obj, ip = False):
    cookie = PoorSession(req)
    # so cookie is not so long, just less then 500 chars 
    cookie.data["data"] = (obj.__class__, obj.__dict__)
    cookie.data["timestamp"] = int(time())
    if ip:
        cookie.data["ip"] = req.get_remote_host()
    cookie.header(req, req.headers_out)
    req.log_error("Login cookie was be set.", state.LOG_INFO)
#enddef

def do_logout(req):
    cookie = PoorSession(req)
    if not "data" in cookie.data:
        req.log_error("Login cookie not found.", state.LOG_INFO)
        return

    cookie.destroy()
    cookie.header(req, req.headers_out)
    req.log_error("Login cookie was be destroyed (Logout).", state.LOG_INFO)
#enddef

def check_login(req, redirect_uri = None):
    req.login = None
    cookie = PoorSession(req)
    if not "data" in cookie.data:
        req.log_error("Login cookie not found.", state.LOG_INFO)
        if redirect_uri:
            redirect(req, redirect_uri)
        return None

    if "ip" in cookie.data and cookie.data["ip"] != req.get_remote_host():
        cookie.destroy()
        cookie.header(req, req.headers_out)
        req.log_error("Login cookie was be destroyed (invalid IP address)",
                state.LOG_INFO)
        if redirect_uri:
            redirect(req, redirect_uri)
        return None

    __class__, __dict__ = cookie.data["data"]
    req.login = __class__()
    req.login.__dict__ = __dict__
    # TODO: req.login.__check__() check cross to DB ??
    cookie.header(req, req.headers_out)     # refresh cookie

    return req.login
#enddef

def check_right(req, right, redirect_uri = '/'):
    if not right in req.login.rights:
        redirect(req, redirect_uri)
#enddef

def check_admin(req, right, redirect_uri = '/'):
    if 'admin' in req.login.rights or right in req.login.rights:
        return
    redirect(req, redirect_uri)
#enddef

def sha1_sdigest(text, salt):
    return sha1(salt + text + "0nb\xc5\x99e!\xc5\xa4\xc5\xafm@").hexdigest()
