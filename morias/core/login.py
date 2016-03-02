# -*- coding: utf-8 -*-

from poorwsgi import state, redirect, SERVER_RETURN
from poorwsgi.session import PoorSession

from time import time
from os import urandom

from falias.util import Object

import csrf

"""
    super - super user, which can averything
    admin - view admin section
    user  - is logged
    guest - annonymous visitor (not logged)
"""
rights = set()
rights.update(('super', 'admin', 'user', 'guest'))


def create_referer(req, referer):
    return "%s://%s%s" % (req.scheme, req.hostname, referer)


def do_login(req, obj, ip=False):
    cookie = PoorSession(req, compress=None)
    # so cookie is not so long, just less then 500 chars
    cookie.data["data"] = (obj.__class__, obj.__dict__)
    cookie.data["timestamp"] = int(time())
    cookie.data["token"] = urandom(24)
    if ip:
        cookie.data["ip"] = req.get_remote_host()
    cookie.header(req, req.headers_out)
    req.log_error("Login cookie was be set.", state.LOG_INFO)
# enddef


def do_logout(req):
    cookie = PoorSession(req, compress=None)
    if "data" not in cookie.data:
        req.log_error("Login cookie not found.", state.LOG_INFO)
        return

    cookie.destroy()
    cookie.header(req, req.headers_out)
    req.log_error("Login cookie was be destroyed (Logout).", state.LOG_INFO)
# enddef


def do_check_login(req):
    req.login = None
    cookie = PoorSession(req, compress=None)
    if "data" not in cookie.data:
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
    req.user_hash = cookie.data['token']

    if not req.login.check(req):
        cookie.destroy()
        req.login = None
        req.log_error("Login cookie was be destroyed (check failed)",
                      state.LOG_INFO)

    cookie.header(req, req.headers_out)     # refresh cookie
    return req.login
# enddef


def do_check_mgc(req):
    """Check Morias Guest Cookie.

    Check guest cookie and set req.user_hash. If no cookie was readed, or will
    be bad. Create new cookie and send it to browser.

    Return value:
        Returun None, if req.login exist yet. So no guest cookie could be used.
        Returun True, if cookie will be readed or False if be created.
    """
    if getattr(req, 'login'):
        return None     # req.login exist - user cookie exist
    cookie = PoorSession(req, SID='MGC')    # Morias Guest Cookie

    if "token" not in cookie.data:
        req.log_error("Creating new cookie.", state.LOG_INFO)
        cookie.data["timestamp"] = int(time())
        cookie.data["token"] = urandom(24)
        req.user_hash = cookie.data["token"]
        cookie.header(req, req.headers_out)
        return False

    req.user_hash = cookie.data["token"]
    return True


def do_check_right(req, right):
    return right in req.login.rights or 'super' in req.login.rights


def do_match_right(req, rights):
    if 'login' not in req.__dict__ or req.login is None \
            or 'rights' not in req.login.__dict__:
        req_login_rights = ('guest',)   # guest is default user right
    else:
        req_login_rights = req.login.rights

    if not rights or 'super' in req_login_rights:
        return True                 # not rights means means login have right

    if not set(req_login_rights).intersection(rights):
        return False                # no rights match

    return True                     # some rights match
# enddef


def do_check_origin(req):
    """ Origin Header must be right (which can't be) or Referer must be OK """
    origin = "%s://%s" % (req.scheme, req.hostname)
    if 'Origin' in req.headers_in:      # could not be!
        return req.headers_in.get('Origin') == origin
    if req.referer is not None:         # referer domain must be same as Host
        referer = req.referer[:req.referer.find('/',
                                                req.referer.find('/') + 2)]
        return referer == origin
    return False


def do_create_token(req, uri):
    """Creates token for uri."""
    if isinstance(uri, unicode):
        uri = uri.encode('utf-8')
    return csrf.get_token(req.secret_key, req.user_hash,
                          create_referer(req, uri))


def do_check_token(req, token, uri=None):
    """Check token creates by do_create_token."""
    if req.referer is None and uri is None:
        return False
    if uri:
        referer = create_referer(req, uri)
    else:
        referer = req.referer.split('?')[0]
    if isinstance(referer, unicode):
        referer = referer.encode('utf-8')
    return csrf.check_token(token, req.secret_key, req.user_hash, referer)


def check_login(req, redirect_uri=None):
    if req.login is None:       # do_check_login was called averytime
        if redirect_uri is None:
            redirect_uri = "/log_in?referer=%s" % req.uri
        redirect(req, redirect_uri)


def check_right(req, right, redirect_uri=None):
    if not do_check_right(req, right):
        req.log_error("Right %s not check" % right, state.LOG_ALERT)
        if redirect_uri:
            redirect(req, redirect_uri)
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)


def match_right(req, rights, redirect_uri=None):
    if not do_match_right(req, rights):
        req.log_error("Rights %s not match" % rights, state.LOG_ALERT)
        if redirect_uri:
            redirect(req, redirect_uri)
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)


def check_referer(req, uri, redirect=None):
    full_referer = create_referer(req, uri)
    if not req.referer or full_referer != req.referer.split('?')[0]:
        req.log_error("Referer %s not check" % uri, state.LOG_ALERT)
        if redirect:
            redirect(req, redirect)
        req.precondition = Object()
        req.precondition.referer = full_referer
        raise SERVER_RETURN(state.HTTP_PRECONDITION_FAILED)
# enddef


def check_origin(req, redirect=None):
    if not do_check_origin(req):
        req.log_error("Origin not check", state.LOG_ALERT)
        if redirect:
            redirect(req, redirect)
        req.precondition = Object()
        req.precondition.origin = "%s://%s" % (req.scheme, req.hostname)
        raise SERVER_RETURN(state.HTTP_PRECONDITION_FAILED)


def create_token(req):
    """Create token for req.uri"""
    return do_create_token(req, req.uri.encode('utf-8'))


def check_token(req, token, redirect=None, uri=None):
    if not do_check_token(req, token, uri):
        req.log_error("Token {0!r} not check".format(token), state.LOG_ALERT)
        if redirect:
            redirect(req, redirect)
        req.precondition = Object()
        req.precondition.csrf = True
        raise SERVER_RETURN(state.HTTP_PRECONDITION_FAILED)
