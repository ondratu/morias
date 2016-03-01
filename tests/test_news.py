from sys import path as python_path
from os import path
from logging import error

from pytest import fixture

sql_path = path.abspath(
    path.join(path.dirname(__file__), path.pardir+'/sql/sqlite'))

python_path.insert(0, path.abspath(
    path.join(path.dirname(__file__), path.pardir+'/tests')))
python_path.insert(0, path.abspath(
    path.join(path.dirname(__file__), path.pardir+'/morias')))

from falias.util import Object
from falias.sql import Sql

from lib.pager import Pager
from lib.new import New


def sql_script(c, sql_script):
    with open(sql_path+'/'+sql_script) as f:
        error('SQL << %s' % f.name)
        c.executescript(f.read())


@fixture()
def req():
    obj = Object()
    obj.db = Sql('sqlite:memory:')
    obj.log_info = error
    with obj.db.transaction(error) as c:
        sql_script(c, 'login.sql')
        sql_script(c, 'logins.01.sql')
        sql_script(c, 'logins.02.sql')
        sql_script(c, 'new.sql')
        sql_script(c, 'news.01.sql')
    return obj


@fixture
def new(req, request):
    new = New()
    new.title = u'Title'
    new.body = u'perex'
    new.public = True
    new.author_id = 1
    new.locale = ''
    new.state = 0
    new.data = {}
    new.add(req)
    return new


def test_db(req):
    New.test(req)


def test_add(req, new):
    assert new.id > 0


def test_get(req, new):
    second = New(new.id)
    second.get(req)
    for attr in ('id', 'title', 'body', 'author_id', 'locale', 'state',
                 'data'):
        assert getattr(new, attr) == getattr(second, attr)


def test_mod(req, new):
    new.title = 'Super title'
    new.mod(req)
    second = New(new.id)
    second.get(req)
    assert new.title == second.title


def test_state(req, new):
    new.set_state(req, 1)
    second = New(new.id)
    second.get(req)
    assert second.state == 1


def test_list(req, new):
    items = New.list(req, Pager(), body=True, state=0)
    assert len(items) == 1
    items = New.list(req, Pager(), body=True, state=1)
    assert len(items) == 0
