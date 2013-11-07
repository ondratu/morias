# -*- coding: utf-8 -*-

from poorwsgi import state
from poorwsgi.session import PoorSession

from time import time
from hashlib import sha1

rights = ['right_admin','right_user', 'right_guest']

def do_login(req, data, ip = None):
    cookie = PoorSession(req)
    cookie.data["data"] = data
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

    req.login = cookie.data["data"]
    cookie.header(req, req.headers_out)     # refresh cookie

    return req.login
#enddef

def check_right(req, right, redirect_uri = '/'):
    if not right in req.login.rights:
        redirect(req, redirect_uri)
#enddef

def sha1_sdigest(text, salt):
    return sha1(salt + text + "0nb\xc5\x99e!\xc5\xa4\xc5\xafm@").hexdigest()
