
from falias.util import uni
from PythonMagick import Image, Blob
from PythonMagick._PythonMagick import Geometry

from hashlib import md5, sha512
from random import seed
from time import time
from mimetypes import guess_extension
from os import makedirs, rename, remove
from os.path import dirname, exists, getmtime
from datetime import datetime

# errors
NO_FILE = 1
EMPTY_OBJECT_TYPE = 2
EMPTY_OBJECT_ID = 3

errors = {NO_FILE: 'no_file', EMPTY_OBJECT_TYPE: 'empty_object_type',
          EMPTY_OBJECT_ID: 'empty_object_id'}

_drivers = ("sqlite",)
_image_exts = ['.jpe', '.png']

seed()


def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "attachments_" + req.db.driver
    return __import__("morias.lib." + m).lib.__getattribute__(m)


class Attachment(object):
    def __init__(self, id=None, md5=None, mime_type=None):
        self.id = id
        self.md5 = md5
        self.mime_type = mime_type

    def get(self, req):
        m = driver(req)
        return m.get(self, req)

    def add(self, req):
        if 'file' not in self.__dict__:
            return NO_FILE
        if not self.object_type:
            return EMPTY_OBJECT_TYPE
        if not self.object_id:
            return EMPTY_OBJECT_ID

        m = driver(req)
        return m.add(self, req)

    def mod(self, req):
        pass    # TODO

    def detach(self, req, object_type, object_id):
        m = driver(req)
        return m.detach(self, req, object_type, object_id)

    def delete(self, req):
        m = driver(req)
        if m.get(self, req) is None:
            return None
        return m.delete(self, req)

    def bind(self, form, uploader_id):
        if 'attachment' in form:
            form_file = form['attachment']
            self.file_name = form_file.filename
            self.mime_type = form_file.type
            self.file = form_file.file
        self.object_type = form.getfirst('object_type', '', uni)
        self.object_id = form.getfirst('object_id', '0', int)
        self.uploader_id = uploader_id
        self.md5 = md5(str(time())).hexdigest()
        self.data = {
            'description': form.getfirst('description', '', uni)
        }

    def dumps(self):
        return {
            'file_name': getattr(self, 'file_name', ''),
            'mime_type': getattr(self, 'mime_type', ''),
            'object_type': getattr(self, 'object_type', ''),
            'object_id': getattr(self, 'object_id', 0),
            'description': getattr(self, 'data', {}).get('description', ''),
            'webname': self.webname()
        }

    def webname(self):
        hex_id = "%06x" % self.id
        return "%s/%s_%s%s" % (hex_id[:-3], hex_id, self.md5[:6],
                               guess_extension(self.mime_type) or '')

    def check_md5(self, webname):
        try:
            return webname.split('_')[1] == self.md5[:6]
        except:
            return False

    def resize_hash(self, size):
        return sha512(self.md5+size).hexdigest()[20:40]

    @staticmethod
    def web_to_id(webname):
        return int(webname.split('_')[0], 16)

    def save(self, req):
        file_path = req.cfg.attachments_path + '/' + self.webname()
        if not exists(dirname(file_path)):
            makedirs(dirname(file_path))

        with open(file_path + '.new', 'w+') as new:
            if not hasattr(self.file, '__exit__'):  # for Python 2.x Only
                new.write(self.file.read())     # cStringIO when file is text
            else:
                with self.file as tmp:
                    new.write(tmp.read())
        rename(file_path + '.new', file_path)

        self.thumb(req)
    # enddef

    def remove(self, req):
        thumb_path = req.cfg.attachments_thumb_path + '/' + self.webname()
        if exists(thumb_path):
            remove(thumb_path)      # remove thumb if exist

        file_path = req.cfg.attachments_path + '/' + self.webname()
        remove(file_path)           # remove original
    # enddef

    def thumb(self, req):
        if self.mime_type.startswith('image') \
                and guess_extension(self.mime_type) in _image_exts:

            file_path = req.cfg.attachments_path + '/' + self.webname()
            img = Image(file_path.encode('utf-8'))

            width, height = req.cfg.attachments_thumb_size.get()
            img.scale(Geometry(width, height))

            thumb_path = req.cfg.attachments_thumb_path + '/' + self.webname()
            if not exists(dirname(thumb_path)):
                makedirs(dirname(thumb_path))
            img.write(thumb_path.encode('utf-8'))
    # enddef

    def resize(self, req, width, height):
        file_path = req.cfg.attachments_path + '/' + self.webname()
        if self.mime_type.startswith('image') \
                and guess_extension(self.mime_type) in _image_exts:

            img = Image(file_path.encode('utf-8'))
            img.fileName(
                'image.'+self.file_name.encode('utf-8').split('.')[-1])
            size = img.size()

            blob = Blob()
            if width > size.width() and height > size.height():
                img.write(blob)
            else:
                img.scale(Geometry(width, height))
                img.write(blob)
            return blob.data
        elif guess_extension(self.mime_type) == '.svg':
            with open(file_path.encode('utf-8'), 'rb') as svg:
                return svg.read()
        else:
            req.log_error(self.mime_type)
            return None
    # enddef

    @staticmethod
    def last_modified(req, webname):
        try:
            file_path = (req.cfg.attachments_path + '/' +
                         webname.split('_')[0][:-3] + '/' + webname)
            return datetime.utcfromtimestamp(int(getmtime(file_path)))
        except OSError as e:
            req.log_error(e)
            return None
    # enddef

    def __del__(self):
        if 'file' in self.__dict__ and not self.file.closed:
            self.file.close()

    @staticmethod
    def list(req, pager, **kwargs):
        if pager.order not in ('timestamp', 'filename', 'mime_type'):
            pager.order = 'timestamp'

        m = driver(req)
        return m.item_list(req, pager, **kwargs)

    @staticmethod
    def list_images(req):
        m = driver(req)
        return m.item_list_images(req)

    @staticmethod
    def error(err):
        return errors.get(err, 'unknow')
# endclass
