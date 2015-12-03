from poorwsgi import app, state, redirect, SERVER_RETURN
from falias.sql import Sql
from falias.util import Object
from falias.smtp import Smtp

from traceback import format_exc
from random import randint

from core.render import generate_page, morias_template
from core.login import rights, do_login, do_logout, check_login, check_referer, \
    check_right
from core.robot import robot_questions

from lib.menu import Item
from lib.pager import Pager
from lib.login import Login, OK, REQUEST_FOR_EMAIL

from admin import system_menu
from user import user_info_menu
from core.errors import BAD_LOGIN

_check_conf = (
    ('morias', 'salt', unicode),                    # salt for passwords
    ('morias', 'db', Sql),                          # database configuration
    ('morias', 'smtp', Smtp),                       # for password reset

    ('login', 'sign_up', bool, False),              # If user could sign up
    # If user could get entry link when don't know password
    ('login', 'forget_password_link', bool, False),
    ('login', 'ttl_of_password_link', int, 30, True,
     'Time to Live in minutes of forgotten password link.'),
    ('login', 'created_verify_link', bool, False, True,
     "If created login must verify his/her email.")
)

module_right = 'users_admin'    # right admin - do anythig with users
R_ADMIN = module_right          # back compatibility

rights.update((R_ADMIN,))

system_menu.append(Item('/admin/logins', label="Logins", symbol='login',
                        rights=[R_ADMIN]))
user_info_menu.append(Item('/login', label="Login", symbol='login',
                           rights=['user']))


def _call_conf(cfg, parser):
    if cfg.login_sign_up:
        app.set_route('/sign_up', sign_up, state.METHOD_GET_POST)
    if cfg.login_forget_password_link:
        app.set_route('/login/forgotten_password', forgotten_password,
                      state.METHOD_GET_POST)


def send_login_created(req, login, sign_up=False):
    try:
        req.smtp.send_email_alternative(
            morias_template(req, 'mail/login/created_subject.jinja',  # subject
                            item=login, sign_up=sign_up).encode('utf-8'),
            login.email,
            morias_template(req, 'mail/login/created.jinja',          # body
                            item=login, sign_up=sign_up).encode('utf-8'),
            morias_template(req, 'mail/login/created.html',           # body
                            item=login, sign_up=sign_up).encode('utf-8'),
            logger=req.logger)
    except Exception:
        req.log_error('Login created [%s] error: \n%s' %
                      (login.email, format_exc()), state.LOG_ERR)
# enddef


def send_log_in_link(req, login, host, browser):
    try:
        req.smtp.send_email_alternative(
            morias_template(req, 'mail/login/log_in_link_subject.jinja',
                            item=login, host=host, browser=browser
                            ).encode('utf-8'),
            login.email,
            morias_template(req, 'mail/login/log_in_link.jinja',        # body
                            item=login, host=host, browser=browser
                            ).encode('utf-8'),
            morias_template(req, 'mail/login/log_in_link.html',         # body
                            item=login, host=host, browser=browser
                            ).encode('utf-8'),
            logger=req.logger)
    except:
        req.log_error('Log-in link [%s] error: \n%s' %
                      (login.email, format_exc()), state.LOG_ERR)
        raise
# enddef


def send_verify_email(req, login, old_email, host, browser):
    try:
        req.smtp.send_email_alternative(
            morias_template(req, 'mail/login/verify_subject.jinja',  # subject
                            item=login, old_email=old_email, host=host,
                            browser=browser).encode('utf-8'),
            login.email,
            morias_template(req, 'mail/login/verify.jinja',          # body
                            item=login, old_email=old_email, host=host,
                            browser=browser).encode('utf-8'),
            morias_template(req, 'mail/login/verify.html',           # body
                            item=login, old_email=old_email, host=host,
                            browser=browser).encode('utf-8'),
            logger=req.logger)
    except Exception:
        req.log_error('Login forget [%s] error: \n%s' %
                      (login.email, format_exc()), state.LOG_ERR)
# enddef


@app.route("/test/logins/db")
def test_db(req):
    data = (None, 123, 3.14, "user@domain.xy", "'; SELECT 1; SELECT")
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT %s, %s, %s, %s, %s", data)
    copy = tuple(it.encode('utf-8') if isinstance(it, unicode) else it
                 for it in c.fetchone())
    tran.commit()

    req.content_type = "text/plain; charset=utf-8"
    if copy == data:
        return "Test Ok\n" + str(data) + '\n' + str(copy)
    else:
        return "Test failed\n" + str(data) + '\n' + str(copy)
# enddef


@app.route('/test/sign_up')
def test_sign_up(req):
    return generate_page(req, "/login/waiting_for_verification.html",
                         item=Object(email='email@domain.xy'))


@app.route('/test/login/verify')
def test_verify(req):
    return generate_page(req, "/login/email_verificated.html")


@app.route('/log_in', method=state.METHOD_GET_POST)
def login(req):
    referer = req.args.getfirst('referer', '', str)

    data = Object(referer=referer, email='')

    if req.method == 'POST':
        login = Login()
        login.bind(req.form, req.cfg.morias_salt)

        ip = 'ip' in req.form
        if login.find(req):
            do_login(req, login.simple(), ip)
            if referer:
                redirect(req, referer)
            if 'admin' in login.rights or 'super' in login.rights:
                redirect(req, '/admin')
            redirect(req, '/')

        data.ip = ip
        data.email = login.email
        data.error = BAD_LOGIN

    return generate_page(req, "login.html", data=data,
                         sign_up=req.cfg.login_sign_up,
                         password_link=req.cfg.login_forget_password_link)
# enddef


@app.route('/log_out')
def logout(req):
    do_logout(req)
    redirect(req, req.referer or '/')
# enddef


@app.route('/admin/logins')
def admin_logins(req):
    check_login(req)
    check_right(req, R_ADMIN)

    error = req.args.getfirst('error', 0, int)

    pager = Pager(sort='asc', order='email')
    pager.bind(req.args)

    rows = Login.list(req, pager)
    return generate_page(req, "admin/logins.html",
                         pager=pager, rows=rows, error=error)
# enddef


@app.route('/admin/logins/add', method=state.METHOD_GET_POST)
def admin_logins_add(req):
    check_login(req)
    check_right(req, R_ADMIN)

    if req.method == 'POST':
        login = Login()
        login.bind(req.form, req.cfg.morias_salt)
        if not req.cfg.login_created_verify_link:
            login.enabled = 1
        login.rights = ['user']
        error = login.add(req)

        if error:
            return generate_page(req, "admin/logins_mod.html",
                                 rights=rights,
                                 item=login, error=error)

        if req.cfg.login_created_verify_link:
            send_login_created(req, login)
        redirect(req, '/admin/logins/%d' % login.id)
    # endif

    return generate_page(req, "admin/logins_mod.html",
                         rights=rights)
# enddef


@app.route('/admin/logins/<id:int>', state.METHOD_GET_POST)
def admin_logins_mod(req, id):
    check_login(req)
    check_right(req, R_ADMIN)

    login = Login(id)
    if req.login.id == login.id:                    # not good idea to remove
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)   # rights himself

    done = None
    if req.method == 'POST':
        login.bind(req.form, req.cfg.morias_salt)
        done = login.mod(req)

        if 0 < done < 64:
            return generate_page(req, "admin/logins_mod.html",
                                 rights=rights,
                                 item=login, error=done)
        # endif
    # endif

    if not login.get(req):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)
    return generate_page(req, "admin/logins_mod.html",
                         rights=rights,
                         item=login, state=done)
# enddef


@app.route('/admin/logins/<id:int>/disable', state.METHOD_POST)
@app.route('/admin/logins/<id:int>/enable', state.METHOD_POST)
def admin_logins_enable(req, id):
    check_login(req, '/log_in?referer=/admin/logins')
    check_right(req, R_ADMIN)
    check_referer(req, '/admin/logins')

    login = Login(id)
    if req.login.id == login.id:                    # not good idea to
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)   # disable himself

    login.enabled = int(req.uri.endswith('/enable'))
    login.enable(req)
    redirect(req, '/admin/logins')
# enddef


@app.route('/login', state.METHOD_GET_POST)
def login_mod(req):
    check_login(req)

    login = Login(req.login.id)

    state = None
    if req.method == 'POST':
        login.bind(req.form, req.cfg.morias_salt)
        email = login.email if login.email != req.login.email else None
        state = login.pref(req, email=email)

        if 0 < state < 64:
            return generate_page(req, "login/login_mod.html",
                                 item=login, error=state)

        state = 0 if state is None else state
        if email:
            host = "%s (%s)" % (req.remote_host, req.remote_addr)
            send_verify_email(req, login, req.login.email, host=host,
                              browser=req.user_agent)
            state |= REQUEST_FOR_EMAIL
    else:
        email = None
    # endif

    login.get(req)
    req.login = login
    return generate_page(req, "login/login_mod.html",
                         item=login, state=state, email=email)
# enddef


def sign_up(req):
    if req.method == 'POST':
        robot = True if req.form.getfirst("robot", "", str) else False
        qid = int(req.form.getfirst("qid", '0', str), 16)
        question, answer = robot_questions[qid]
        check = req.form.getfirst("answer", "", str) == answer

        login = Login()
        login.bind(req.form, req.cfg.morias_salt)

        if robot or not check:
            return generate_page(req, "/login/login_mod.html", item=login,
                                 question=question, answer=answer, check=check,
                                 qid=hex(qid), form=req.form)

        error = login.add(req, True)
        if error:
            return generate_page(
                req, "/login/login_mod.html", item=login, error=error,
                question=question, answer=answer, check=check, qid=hex(qid),
                form=req.form,
                password_link=req.cfg.login_forget_password_link)

        send_login_created(req, login)
        return generate_page(req, "/login/waiting_for_verification.html",
                             item=login)
    # endif

    qid = randint(0, len(robot_questions)-1)
    question, answer = robot_questions[qid]
    return generate_page(req, "/login/login_mod.html", item=Object(),
                         question=question, answer=answer, qid=hex(qid),
                         form=Object())


@app.route('/login/verify/<servis_hash:hex>')
def verify(req, servis_hash):
    login = Login()
    status = login.verify(req, servis_hash)
    if status is True:
        do_login(req, login.simple())
        redirect(req, '/')
    elif status == OK:
        return generate_page(req, "/login/email_verificated.html")
    else:
        return generate_page(req, "/login/email_verificated.html",
                             error=status, item=login)
# enddef


def forgotten_password(req):
    if req.method == 'POST':
        robot = True if req.form.getfirst("robot", "", str) else False
        qid = int(req.form.getfirst("qid", '0', str), 16)
        question, answer = robot_questions[qid]
        check = req.form.getfirst("answer", "", str) == answer

        login = Login()
        login.email = req.form.getfirst("email", "", str).strip()

        if robot or not check or not login.check_email():
            return generate_page(req, "/login/forgotten_password.html",
                                 ttl=req.cfg.login_ttl_of_password_link,
                                 form=req.form, question=question,
                                 answer=answer, check=check, qid=hex(qid))

        login.log_in_link(req)
        host = "%s (%s)" % (req.remote_host, req.remote_addr)
        send_log_in_link(req, login, host=host, browser=req.user_agent)
        return generate_page(req, "/login/verify_link_send.html", item=login)

    qid = randint(0, len(robot_questions)-1)
    question, answer = robot_questions[qid]
    return generate_page(req, "/login/forgotten_password.html",
                         ttl=req.cfg.login_ttl_of_password_link, form=Object(),
                         question=question,  answer=answer, qid=hex(qid))
