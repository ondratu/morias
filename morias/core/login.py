# -*- coding: utf-8 -*-

from poorwsgi import state, redirect, SERVER_RETURN
from poorwsgi.session import PoorSession

from time import time
from hashlib import sha1

from falias.util import Object

rights = ['super', 'admin', 'user', 'guest']

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

def do_check_login(req):
    req.login = None
    cookie = PoorSession(req)
    if not "data" in cookie.data:
        req.log_error("Login cookie not found.", state.LOG_INFO)
        return None

    if "ip" in cookie.data and cookie.data["ip"] != req.get_remote_host():
        cookie.destroy()
        cookie.header(req, req.headers_out)
        req.log_error("Login cookie was be destroyed (invalid IP address)",
                state.LOG_INFO)
        return None

    __class__, __dict__ = cookie.data["data"]
    req.login = __class__()
    req.login.__dict__ = __dict__.copy()
    
    if not req.login.check(req):
        cookie.destroy()
        cookie.header(req, req.headers_out)
        req.log_error("Login cookie was be destroyed (check failed)",
                state.LOG_INFO)
        return None

    cookie.header(req, req.headers_out)     # refresh cookie
    return req.login
#enddef

def do_check_right(req, right):
    return right in req.login.rights or 'super' in req.login.rights


def do_match_right(req, rights):
    if not 'login' in req.__dict__ or req.login is None or not 'rights' in req.login.__dict__:
        req_login_rights = ('guest',)   # guest is default user right
    else:
        req_login_rights = req.login.rights

    if not rights or 'super' in req_login_rights:
        return True                     # not rights means means login have right

    if not set(req_login_rights).intersection(rights):
        return False                    # no rights match

    return True                         # some rights match
#enddef

def check_login(req, redirect_uri = None):
    if do_check_login(req) is None:
        if redirect_uri is None:
            redirect_uri = "/login?referer=%s" % req.uri
        redirect(req, redirect_uri)


def check_right(req, right, redirect_uri = None):
    if not do_check_right(req, right):
        if redirect_uri:
            redirect(req, redirect_uri)
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)


def match_right(req, rights, redirect_uri = None):
    if not do_match_right(req, rights):
        if redirect_uri:
            redirect(req, redirect_uri)
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)


def check_referer(req, referer, redirect = None):
    full_referer = "%s://%s%s" % (req.scheme, req.hostname, referer)
    if full_referer != req.referer.split('?')[0]:
        if redirect:
            redirect(req, redirect)
        req.precondition = Object()
        req.precondition.referer = full_referer
        raise SERVER_RETURN(state.HTTP_PRECONDITION_FAILED)
#enddef

def sha1_sdigest(text, salt):
    #return sha1(salt + text + "0nb\xc5\x99e!\xc5\xa4\xc5\xafm@").hexdigest()
    return sha1((salt + text + u'0nb\u0159e!\u0164\u016fm@').encode('utf-8')).hexdigest()
