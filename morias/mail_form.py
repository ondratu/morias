from poorwsgi import app, state

from falias.smtp import Smtp, Email
from falias.util import Object, uni, Paths
from random import seed, randint

from core.render import generate_page, morias_template
from core.robot import robot_questions
from core.lang import get_lang

seed()

_check_conf = (
    ('morias', 'smtp', Smtp),

    # path to web templates relative to templates
    ('form', 'web_templates', unicode, 'forms'),
    # path to mail templates relative to templates
    ('form', 'mail_templates', unicode, 'mail'),
    ('form', 'recipient', Email),           # default form recipient
    ('form', 'paths', Paths),               # list of paths
)


def _call_conf(cfg, parser):
    cfg.form_web_templates += '/'
    cfg.form_mail_templates += '/'

    if cfg.form_paths:
        cfg.forms = {}

    for uri in cfg.form_paths:
        app.set_route('/form/' + uri.encode('utf-8'),
                      form_send, state.METHOD_GET_POST)

        f = Object()
        f.template = parser.get('form_%s' % uri, 'template')
        f.required = parser.get('form_%s' % uri, 'required', '', tuple)
        f.protection = parser.get('form_%s' % uri, 'protection', True, bool)
        f.answer = parser.get('form_%s' % uri, 'answer', '')
        f.recipient = parser.get('form_%s' % uri, 'recipient',
                                 cfg.form_recipient)
        f.subject = parser.get('form_%s' % uri, 'subject',
                               cfg.site_name + ': ' + uri)

        cfg.forms[uri] = f
# enddef


def form_send(req):
    locale = req.args.getfirst('locale', get_lang(req), uni)
    menu = req.cfg.get_static_menu(req)
    fdict = dict((key, uni(req.form.getvalue(key))) for key in req.form.keys())

    form_obj = req.cfg.forms[req.uri.split('/')[-1]]
    qid, question, answer = (0, '', form_obj.answer)
    status = None

    if req.method == 'POST':
        if form_obj.protection:
            robot = True if req.form.getfirst("robot", "", str) else False
            if not form_obj.answer:
                qid = int(req.form.getfirst("qid", '0', str), 16)
                question, answer = robot_questions[qid]

            check = req.form.getfirst("answer", "", str) == answer
        else:
            robot = False
            check = True
        # endif

        required = []
        # check email if exist
        if 'email' in req.form:
            if not Email.check(req.form.getfirst("email", fce=str)):
                required.append('email')

        for it in form_obj.required:
            if it not in req.form:
                required.append(it)

        if robot or not check or required:
            return generate_page(
                req, req.cfg.form_web_templates + form_obj.template + '.html',
                question=question, answer=answer, qid=hex(qid), form=fdict,
                menu=menu, lang=locale, required=required, robot=robot,
                check=check)
        # else
        kwargs = {'logger': req.logger}
        if 'email' in req.form:
            kwargs['reply'] = req.form.getfirst('email', '', str)

        status = False
        try:
            req.smtp.send_email_txt(
                form_obj.subject,                       # subject
                form_obj.recipient,                     # recipient
                morias_template(
                    req,
                    req.cfg.form_mail_templates + form_obj.template + '.txt',
                    form=fdict).encode('utf-8'),        # body
                **kwargs)                               # logger + reply
            fdict = {}
            status = True
        except Exception as e:
            req.log_error('Mail form: %s', str(e), state.LOG_ERROR)
            status = False

    # else (reg.method != POST)
    if form_obj.protection and not form_obj.answer:
        qid = randint(0, len(robot_questions)-1)
        question, answer = robot_questions[qid]

    return generate_page(
        req, req.cfg.form_web_templates + form_obj.template + '.html',
        question=question, answer=answer, qid=hex(qid), form=fdict, menu=menu,
        lang=locale, status=status)
# enddef
