# -*- coding: utf-8 -*-
from sys import path as python_path
from os import path
from logging import error

from pytest import fixture, main

sql_path = path.abspath(
    path.join(path.dirname(__file__), path.pardir+'/sql/sqlite'))

python_path.insert(0, path.abspath(
    path.join(path.dirname(__file__), path.pardir+'/tests')))
python_path.insert(0, path.abspath(
    path.join(path.dirname(__file__), path.pardir+'/morias')))
python_path.insert(0, path.abspath(
    path.join(path.dirname(__file__), path.pardir)))

from support.sqlite import sql_script
from support.form import Form

from falias.util import Object
from falias.sql import Sql

from morias.lib.pager import Pager
from morias.lib.redirects import Redirect, EmptySrc, EmptyDst, BadCode


@fixture()
def req():
    obj = Object()
    obj.cfg = Object(redirects_timestamp='/dev/null')
    obj.db = Sql('sqlite:memory:')
    obj.log_info = error
    obj.log_error = error
    with obj.db.transaction(error) as c:
        sql_script(c, sql_path, 'redirects.sql')
    return obj


@fixture
def redirect(req):
    item = Redirect()
    form = Form((('src', '/'),
                 ('dst', '/test'),
                 ('code', 301)))
    item.bind(form)
    assert item.add(req) is not None
    return item


class TestRedirect:

    def test_db(self, req):
        Redirect.test(req)

    def test_add(self, req, redirect):
        item = Redirect()
        item.state = 1
        assert isinstance(item.add(req), EmptySrc)
        item.src = '/'
        assert isinstance(item.add(req), EmptyDst)
        item.dst = '/root'
        assert isinstance(item.add(req), BadCode)
        item.code = 301
        assert item.add(req) is None

    def test_get(self, req, redirect):
        item = Redirect(redirect.id)
        assert item.get(req) is not None
        assert item.src == redirect.src
        assert item.dst == redirect.dst
        assert item.code == redirect.code
        assert item.state == redirect.state

    def test_get_by_src(self, req, redirect):
        item = Redirect(src=redirect.src)
        assert item.get(req, key='src') is not None
        assert item.src == redirect.src
        assert item.dst == redirect.dst
        assert item.code == redirect.code
        assert item.state == redirect.state

    def test_list(self, req, redirect):
        items = Redirect.list(req, Pager(limit=1))
        assert items[0].src == redirect.src

    def test_list_disables(self, req, redirect):
        items = Redirect.list(req, Pager(limit=1), state=0)
        assert items[0].src == redirect.src

if __name__ == '__main__':
    main(['-v', __file__])
