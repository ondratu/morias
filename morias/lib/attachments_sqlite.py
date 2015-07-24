
from falias.util import islistable

import json

from lib.attachments import Attachment

def get(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute("SELECT uploader_id, timestamp, mime_type, file_name, md5, data "
                "FROM attachments WHERE attachment_id = %d", self.id)
    row = c.fetchone()
    if not row:
        return None

    tran.commit()
    self.uploader_id, self.timestamp, self.mime_type, self.file_name, \
                                                        self.md5, data = row
    self.data = json.loads(data)
    return self
#enddef

def add(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    c.execute("INSERT INTO attachments (uploader_id, timestamp, mime_type, "
                    "file_name, md5, data) "
                "VALUES (%d, strftime('%%s','now')*1, %s, %s, %s, %s)",
                (self.uploader_id, self.mime_type, self.file_name,
                self.md5, json.dumps(self.data)) )
    self.id = c.lastrowid
    c.execute("INSERT INTO object_attachments (attachment_id, object_type, "
                    "object_id) VALUES (%d, %s, %d)",
                (self.id, self.object_type, self.object_id))
    self.save(req)
    tran.commit()
    return self
#enddef

def detach(self, req, object_type, object_id):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    c.execute("DELETE FROM object_attachments WHERE "
            "attachment_id = %d AND object_type = %s AND object_id = %d",
            (self.id, object_type, object_id))
    done = c.rowcount
    tran.commit()
    return (done == 1)
#enddef

def delete(self, req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()

    c.execute("SELECT count(attachment_id) FROM object_attachments "
            "WHERE attachment_id = %d", self.id)
    count = c.fetchone()[0]

    if count == 0:
        c.execute("DELETE FROM attachments WHERE attachment_id = %d", self.id)
        self.remove(req)
    else:
        req.logger("Just another (%d) uses of attachment %d" % (count, self.id))

    tran.commit()
    return count
#enddef

def item_list(req, pager, **kwargs):
    n = 'NOT ' if kwargs.pop('NOT', False) else ''
    keys = list( "%s %s %%s" % (k, 'IN' if islistable(v) else '=') for k,v in kwargs.items() )
    cond = "WHERE %s(%s)" % (n, ' AND '.join(keys)) if keys else ''

    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute(
        "SELECT "
            "a.attachment_id, a.uploader_id, a.timestamp, a.mime_type, "
            "a.file_name, a.md5, a.data, l.email, o.object_type "
        "FROM attachments a "
            "LEFT JOIN object_attachments o ON (o.attachment_id = a.attachment_id) "
            "LEFT JOIN logins l ON (l.login_id = a.uploader_id) "
            "%s GROUP BY a.attachment_id ORDER BY %s %s LIMIT %%d, %%d" % \
                (cond, pager.order, pager.sort),
        tuple(kwargs.values()) + (pager.offset, pager.limit))
    items = []
    for row in iter(c.fetchone, None):
        item = Attachment()
        item.id, item.uploader, item.timestamp, item.mime_type, \
                item.file_name, item.md5, data, item.author, \
                                                item.object_type = row
        item.data = json.loads(data)
        items.append(item)
    #endwhile

    c.execute("SELECT count(*) "
        "FROM attachments a "
            "LEFT JOIN object_attachments o ON (o.attachment_id = a.attachment_id) "
            "%s" % cond, kwargs.values())   # FIXME: bad count on object_attachents
    pager.total = c.fetchone()[0]
    tran.commit()

    return items
#enddef

def item_list_images(req):
    tran = req.db.transaction(req.logger)
    c = tran.cursor()
    c.execute(
        "SELECT "
            "attachment_id, uploader_id, timestamp, mime_type, file_name, md5, data "
        "FROM attachments WHERE mime_type %s LIKE 'image%%' ")
    items = []
    for row in iter(c.fetchone, None):
        item = Attachment()
        item.id, item.uploader, item.timestamp, item.mime_type, \
                                    item.file_name, item.md5, data = row
        item.data = json.loads(data)
        items.append(item)
    #endwhile

    tran.commit()
    return items
#enddef
