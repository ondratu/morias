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
from lib.login import Login

from admin import system_menu
from user import user_info_menu
from core.errors import BAD_LOGIN

_check_conf = (
    ('morias', 'salt', unicode),                    # salt for passwords
    ('morias', 'db', Sql),                          # database configuration
    ('morias', 'smtp', Smtp),                       # for password reset
    ('morias', 'sign_up', bool, False, True),       # if users can sign up
)

module_right = 'users_admin'    # right admin - do anythig with users
R_ADMIN = module_right          # back compatibility

rights.update((R_ADMIN,))

system_menu.append(Item('/admin/logins', label="Logins", symbol='login',
                        rights=[R_ADMIN]))
user_info_menu.append(Item('/login', label="Login", symbol='login',
                           rights=['user']))


def _call_conf(cfg, parser):
    if cfg.debug:
        app.set_route('/sign_up', sign_up, state.METHOD_GET_POST)


def send_acount_created(req, login, sign_up=False):
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
        req.log_error('Login acount created [%s] error: \n%s' %
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
        ip = 'ip' in req.form
        login.bind(req.form, req.cfg.morias_salt)
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
                         sign_up=req.cfg.morias_sign_up)
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
        login.enabled = 1
        login.rights = ['user']
        error = login.add(req)

        if error:
            return generate_page(req, "admin/logins_mod.html",
                                 rights=rights,
                                 item=login, error=error)

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

        if done < 100:
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
        state = login.pref(req)

        # TODO: verify new email before changeed...

        if state < 100:
            return generate_page(req, "login/login_mod.html",
                                 item=login, error=state)
        # endif
    # endif

    login.get(req)
    req.login = login
    return generate_page(req, "login/login_mod.html",
                         item=login, state=state)
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
            return generate_page(req, "/login/login_mod.html", item=login,
                                 error=error, question=question, answer=answer,
                                 check=check, qid=hex(qid), form=req.form)

        send_acount_created(req, login)
        # redirect(req, '/log_in')
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
    if not Login.verify(req, servis_hash):
        redirect(req, '/log_in')
    return generate_page(req, "/login/email_verificated.html")
# enddef
