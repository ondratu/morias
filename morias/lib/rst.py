from docutils.core import publish_parts
from docutils_tinyhtml import Writer

from json import dumps
from cStringIO import StringIO

import re

re_message = re.compile(r"[<>\w]+:(\d+): \((\w+)/(\d+)\) (.*)", re.U)


def parse_system_messages(out):
    if not isinstance(out, str):
        out = out.decode()
    retval = set()
    for line in out.split('\n'):
        match = re_message.search(line)
        if match:
            retval.add(match.groups())
    return tuple(retval)


def rst2html(source, err_stream=StringIO()):
    writer = Writer()
    parts = publish_parts(source=source,
                          writer=writer,
                          writer_name='html',
                          settings_overrides={
                              'warning_stream': err_stream,
                              'no_system_messages': True
                          })
    html = parts['html_title'] + parts['body']
    if parts['html_footnotes'] or parts['html_citations']:
        html = parts['html_line'] + \
            parts['html_footnotes'] + parts['html_citations']
    err_stream.seek(0)
    return html


def check_rst(req):
    source = req.form.getfirst('source', '').strip()
    if not source:
        req.content_type = 'application/json'
        return dumps({'status': 200,
                      'errors': [],
                      'html': ''})

    err_stream = StringIO()
    html = rst2html(source, err_stream)
    err_stream.seek(0)
    errors = err_stream.read()

    req.content_type = 'application/json'
    return dumps({'status': 200 if not errors else 202,
                  'errors': parse_system_messages(errors),
                  'html': html})
