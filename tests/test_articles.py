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

from falias.util import Object
from falias.sql import Sql
from poorwsgi.request import Json

from lib.pager import Pager
from lib.articles import Article, FORMAT_RST


def sql_script(c, sql_script):
    with open(sql_path+'/'+sql_script) as f:
        error('SQL << %s' % f.name)
        c.executescript(f.read())


class Form(Json):
    def __init__(self, items):
        dict.__init__(self, items)
        self.getvalue = self.get


@fixture()
def req():
    obj = Object()
    obj.db = Sql('sqlite:memory:', True)
    obj.log_info = error
    with obj.db.transaction(error) as c:
        sql_script(c, 'login.sql')
        sql_script(c, 'logins.01.sql')
        sql_script(c, 'logins.02.sql')
        sql_script(c, 'tags.sql')
        sql_script(c, 'articles.sql')
    return obj


@fixture
def article(req, request):
    article = Article()
    form = Form((('title', u'Title'),
                 ('perex', u'perex'),
                 ('body', u'body'),
                 ('state', 0)))
    article.bind(form, author_id=1)
    assert article.add(req) is None
    return article


def test_db(req):
    Article.test(req)


def test_add(req, article):
    assert article.id > 0


def test_get(req, article):
    second = Article(article.id)
    second.get(req)
    for attr in ('id', 'title', 'perex', 'body', 'serial_id', 'author_id',
                 'locale', 'state', 'data'):
        assert getattr(article, attr) == getattr(second, attr)


def test_mod(req, article):
    article.title = 'Super title'
    article.format = FORMAT_RST
    article.mod(req)
    second = Article(article.id)
    second.get(req)
    assert article.title == second.title
    assert article.format == second.format


def test_state(req, article):
    article.set_state(req, 1)
    second = Article(article.id)
    second.get(req)
    assert second.state == 1


def test_list(req, article):
    items = Article.list(req, Pager(), perex=True, state=0)
    assert len(items) == 1
    items = Article.list(req, Pager(), perex=True, state=1)
    assert len(items) == 0


seo_table = (('Url', 'url'),
             ('some url', 'some_url'),
             ('Some long url:)', 'some_long_url'),
             (' some  spaces  url ', 'some_spaces_url'),
             ('Sony, Microsoft, Apple a jiná monstra',
              'sony_microsoft_apple_a_jina_monstra'),
             ('Vala 5: GTK+ Kontejnery', 'vala_5_gtk_kontejnery'),
             ('10 tipů jak řešit SEO', '10_tipu_jak_resit_seo'),
             ('PoorHttp: PoorWSGI vydán, co dál ?',
              'poorhttp_poorwsgi_vydan_co_dal'))


@fixture(params=seo_table)
def uri_pair(request):
    return request.param


def test_seo_uri(uri_pair):
    assert Article.make_uri(uri_pair[0]) == uri_pair[1]


if __name__ == '__main__':
    main(['-v'])
