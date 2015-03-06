
from hashlib import md5
from random import random, seed
from time import time
from mimetypes import guess_extension
from os import makedirs, rename, remove
from os.path import dirname, exists

from falias.util import uni
from PythonMagick import Image
from PythonMagick._PythonMagick import Geometry

# errors
NO_FILE             = 1
EMPTY_OBJECT_TYPE   = 2
EMPTY_OBJECT_ID     = 3

errors = {  NO_FILE: 'no_file', EMPTY_OBJECT_TYPE: 'empty_object_type',
            EMPTY_OBJECT_ID: 'empty_object_id' }

_drivers = ("sqlite",)
_image_exts = ['.jpe', '.png']

seed()

def driver(req):
    if req.db.driver not in _drivers:
        raise RuntimeError("Uknow Data Source Name `%s`" % req.db.driver)
    m = "attachments_" + req.db.driver
    return __import__("lib." + m).__getattribute__(m)
#enddef

class Attachment(object):
    def __init__(self, id = None):
        self.id = id

    def get(self, req):
        m = driver(req)
        return m.get(self, req)

    def add(self, req):
        if not 'file' in self.__dict__: return NO_FILE
        if not self.object_type: return EMPTY_OBJECT_TYPE
        if not self.object_id: return EMPTY_OBJECT_ID

        m = driver(req)
        return m.add(self, req)
    #enddef

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
            self.file      = form_file.file
        self.object_type = form.getfirst('object_type', '', uni)
        self.object_id   = form.getfirst('object_id', '0', int)
        self.description = form.getfirst('description', '', uni)
        self.uploader_id = uploader_id
        self.data = {
                'md5': md5(str(time())).hexdigest()
            }
        print "object_type", form.keys()
    #enddef

    def dumps(self):
        return {
            'file_name'   : self.__dict__.get('file_name',''),
            'mime_type'   : self.__dict__.get('mime_type',''),
            'object_type' : self.__dict__.get('object_type',''),
            'object_id'   : self.__dict__.get('object_id', 0),
            'description' : self.__dict__.get('description',''),
            'webname'     : self.webname()
        }


    def webname(self):
        hex_id = "%06x" % self.id
        return "%s/%s_%s%s" % (hex_id[:-3], hex_id, self.data['md5'][:6],
                                guess_extension(self.mime_type) or '')

    @staticmethod
    def web_to_id(webname):
        return int(webname.split('_')[0], 16)

    def save(self, req):
        file_path = req.cfg.attachments_path + '/' + self.webname()
        if not exists(dirname(file_path)):
            makedirs(dirname(file_path))

        with open (file_path + '.new', 'w+') as new:
            if not hasattr(self.file, '__exit__'):  # for Python 2.x Only
                new.write(self.file.read())         # cStringIO when file is text
            else:
                with self.file as tmp:
                    new.write(tmp.read())
        rename(file_path + '.new', file_path)

        self.thumb(req)
    #enddef

    def remove(self, req):
        thumb_path = req.cfg.attachments_thumb_path + '/' + self.webname()
        if exists(thumb_path):
            remove(thumb_path)      # remove thumb if exist

        file_path = req.cfg.attachments_path + '/' + self.webname()
        remove(file_path)           # remove original
    #enddef

    def thumb(self, req):
        if self.mime_type.startswith('image') \
            and guess_extension(self.mime_type) in _image_exts:

            file_path = req.cfg.attachments_path + '/' + self.webname()
            img = Image(file_path.encode('utf-8'))
            size = img.size()

            width, height = req.cfg.attachments_thumb_size.get()
            img.scale(Geometry(width, height))

            thumb_path = req.cfg.attachments_thumb_path + '/' + self.webname()
            if not exists(dirname(thumb_path)):
                makedirs(dirname(thumb_path))
            img.write(thumb_path.encode('utf-8'))
    #enddef

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
#endclass
