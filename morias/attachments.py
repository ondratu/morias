# -*- coding: utf-8 -*-

from poorwsgi import app, state, SERVER_RETURN, send_file
from falias.sql import Sql
from falias.util import Size, uni

from datetime import datetime

import json

from core.render import generate_page
from core.login import rights, check_login, check_right, match_right, \
    check_referer, check_origin

from lib.menu import Item
from lib.pager import Pager
from lib.jobs import run_job, Job
from lib.attachments import Attachment

from admin import system_menu

# required
import login
import jobs

__requires = (login, jobs)

_check_conf = (
    ('morias', 'db', Sql),                          # database configuration
    ('attachments', 'path', str),
    ('attachments', 'thumb_path', str, ''),
    ('attachments', 'thumb_size', Size, '320x200', True)
)

R_ADMIN = 'attachments_modify'
module_rights = ['attachments_author', 'attachments_listall', R_ADMIN]
rights.update(module_rights)

system_menu.append(Item('/admin/attachments', label="Attachments",
                        symbol='attachments', rights=module_rights))

app.set_filter('attachment', r'[\w\.]+', uni)
time_format = "%a, %d %b %Y %X GMT"

# TODO: core.test.sql.count (table)
#                    .data ()        # none, number, float, string, unicode
#                    .sqlinjection ()
#                .dirs ((dir, dir))


def js_items(req, **kwargs):
    # size of thumb could be set from request
    thumb_size = req.args.getfirst('thumb_size', '320x200', str)
    pager = Pager(limit=-1)
    items = []
    for item in Attachment.list(req, pager, **kwargs):
        item.webname = item.webname()
        item.resize_hash = item.resize_hash(thumb_size)
        items.append(item.__dict__)
    req.content_type = 'application/json'
    return json.dumps({'items': items})


@app.route('/admin/attachments')
def admin_attachments(req):
    check_login(req)
    check_right(req, R_ADMIN)

    pager = Pager(order='timestamp', sort='desc')
    pager.bind(req.args)

    kwargs = {}

    if 'obty' in req.args:
        kwargs['object_type'] = req.args.getfirst('obty', fce=uni) or None
        pager.set_params(obty=kwargs['object_type'])
    if 'obid' in req.args:
        kwargs['object_id'] = req.args.getfirst('obid', fce=int)
        pager.set_params(obid=kwargs['object_id'])

    rows = Attachment.list(req, pager, **kwargs)
    return generate_page(req, "admin/attachments.html",
                         pager=pager, rows=rows)


@app.route('/admin/attachments/add', method=state.METHOD_POST)
def admin_attachments_add_update(req, id=None):
    check_login(req)
    match_right(req, [R_ADMIN, 'attachments_author'])
    check_origin(req)

    attachment = Attachment()
    attachment.bind(req.form, req.login.id)
    status = attachment.add(req)
    if not status == attachment:
        req.status = state.HTTP_BAD_REQUEST
        req.content_type = 'application/json'
        return json.dumps({'reason': Attachment.error(status)})

    req.content_type = 'application/json'
    return json.dumps({'attachment': attachment.dumps()})


@app.route('/admin/attachments/<object_type:word>/<object_id:int>/<path:word>/'
           '<webid:attachment>/detach', method=state.METHOD_POST)
def attachments_detach(req, object_type, object_id, path, webid):
    check_login(req)
    match_right(req, [R_ADMIN, 'attachments_author'])
    check_origin(req)
    attachment = Attachment(Attachment.web_to_id(webid))
    attachment.detach(req, object_type, object_id)
    if attachment.delete(req) is None:
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    return js_items(req, object_type=object_type, object_id=object_id)


def thumb_images(req, job):
    items = Attachment.list_images(req)
    i, length = 0, len(items)
    for item in items:
        item.thumb(req)
        i += 1
        job.mod(req, progress=i*100/length)


@app.route('/admin/attachments/images/thumb', method=state.METHOD_POST)
def admin_attachments_images_thumb(req):
    check_login(req)
    match_right(req, [R_ADMIN, 'attachments_modify'])
    check_origin(req)

    # job must be singleton
    pid, status = run_job(req, req.uri, thumb_images, True)
    req.content_type = 'application/json'
    if not status:
        req.status = state.HTTP_NOT_ACCEPTABLE
        return '{}'

    req.status = state.HTTP_CREATED
    return json.dumps({'pid': pid})


@app.route('/admin/attachments/images/thumb')
def admin_attachments_images_thumb_check(req):
    check_login(req)
    match_right(req, [R_ADMIN, 'attachments_modify'])
    check_referer(req, '/admin/attachments')

    job = Job(path=req.uri)
    req.content_type = 'application/json'
    if job.get(req):
        req.status = state.HTTP_CREATED
        return json.dumps(job.data)
    return '{}'     # job not found, so it could be run again


@app.route('/admin/attachments/<object_type:word>/<object_id:int>')
def attachments_view(req, object_type, object_id):
    return js_items(req, object_type=object_type, object_id=object_id)


@app.route('/admin/attachments/<object_type:word>/<object_id:int>/not')
def attachments_view_not(req, object_type, object_id):
    check_login(req)
    match_right(req, [R_ADMIN, 'attachments_author'])
    check_origin(req)
    return js_items(req, object_type=object_type, object_id=object_id,
                    NOT=True)


@app.route('/attachments/<path:word>/<webid:attachment>/realname')
def attachments_download(req, path, webid):
    attachment = Attachment(Attachment.web_to_id(webid))
    attachment.get(req)

    req.headers_out.add_header(
        'Content-Disposition',
        'attachment',
        # filename=attachment.file_name.encode('ascii','xmlcharrefreplace'))
        filename=attachment.file_name.encode('ascii', 'backslashreplace'))

    return send_file(req, req.cfg.attachments_path + '/' + path + '/' + webid,
                     content_type=attachment.mime_type)


@app.route('/attachments/<path:word>/<webid:attachment>/'
           '<width:int>x<height:int>')
def attachments_resize(req, path, webid, width, height):
    attachment = Attachment(Attachment.web_to_id(webid))
    last_modified = Attachment.last_modified(req, webid)

    if last_modified is None:                   # file not found
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    if 'If-Modified-Since' in req.headers_in:   # check cache header
        hdt = datetime.strptime(req.headers_in['If-Modified-Since'],
                                time_format)
        if last_modified <= hdt:
            req.headers_out.add_header('Last-Modified',
                                       last_modified.strftime(time_format))
            req.headers_out.add_header('Date',
                                       datetime.utcnow().strftime(time_format))
            raise SERVER_RETURN(state.HTTP_NOT_MODIFIED)

    attachment.get(req)                         # check resize hash
    if req.args.get('hash', '') != attachment.resize_hash("%dx%d" %
                                                          (width, height)):
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)

    retval = attachment.resize(req, width, height)
    if retval is None:                          # it is not image
        raise SERVER_RETURN(state.HTTP_BAD_REQUEST)

    req.content_type = attachment.mime_type
    req.clength = len(retval)
    req.headers_out.add_header('Last-Modified',
                               last_modified.strftime(time_format))
    return retval
attachments_resize.no_check_login = True
# enddef
