from poorwsgi import FieldStorage


def form2class(req, cls):
    form = FieldStorage(req)

