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

from lib.pager import Pager
from lib.articles import Article, FORMAT_RST, ArticleComment


@fixture()
def req():
    obj = Object()
    obj.db = Sql('sqlite:memory:')
    obj.log_info = error
    obj.log_error = error
    with obj.db.transaction(error) as c:
        sql_script(c, sql_path, 'login.sql')
        sql_script(c, sql_path, 'logins.01.sql')
        sql_script(c, sql_path, 'logins.02.sql')
        sql_script(c, sql_path, 'tags.sql')
        sql_script(c, sql_path, 'articles.sql')
        sql_script(c, sql_path, 'articles_discussion.sql')
    return obj


@fixture
def article(req, request=None, title=u'Title'):
    article = Article()
    form = Form((('title', title),
                 ('perex', u'perex'),
                 ('body', u'body'),
                 ('state', 0)))
    article.bind(form, author_id=1)
    assert article.add(req) is None
    return article


class TestArticle:

    def test_db(self, req):
        Article.test(req)

    def test_add(self, req, article):
        assert article.id > 0

    def test_get(self, req, article):
        second = Article(article.id)
        second.get(req)
        for attr in ('id', 'title', 'perex', 'body', 'serial_id', 'author_id',
                     'locale', 'state', 'data'):
            assert getattr(article, attr) == getattr(second, attr)

    def test_mod(self, req, article):
        article.title = 'Super title'
        article.format = FORMAT_RST
        article.mod(req)
        second = Article(article.id)
        second.get(req)
        assert article.title == second.title
        assert article.format == second.format

    def test_state(self, req, article):
        article.set_state(req, 1)
        second = Article(article.id)
        second.get(req)
        assert second.state == 1

    def test_list(self, req, article):
        items = Article.list(req, Pager(), perex=True, state=0)
        assert len(items) == 1
        items = Article.list(req, Pager(), perex=True, state=1)
        assert len(items) == 0


@fixture()
def comment(article, request=None):
    comment = ArticleComment()
    form = Form((('article_id', article.id),
                 ('author', 'Ondřej Tůma'),
                 ('title', u'Title'),
                 ('perex', u'perex'),
                 ('body', u'body'),
                 ('state', 0)))
    comment.bind(form, user_agent='py.test', ip='127.0.0.1')
    return comment


class TestArticleDiscussion:
    def test_bind(self, comment):
        pass

    def test_first_comment(self, req, comment):
        comment.add(req)
        assert comment.id == '1'

    def test_get(self, req, comment):
        comment.add(req)
        second = ArticleComment(comment.id)
        second.object_id = comment.object_id
        second.get(req)
        for attr in ('id', 'object_id', 'author', 'author_id', 'create_date',
                     'title', 'body', 'data'):
            assert getattr(comment, attr) == getattr(second, attr), attr
    # enddef

    def test_tree(self, req, article):
        c1 = comment(article)
        c1.add(req)
        assert c1.id == '1'
        c2 = comment(article)
        c2.add(req)
        assert c2.id == '2'
        c11 = comment(article)
        c11.add(req, '1')
        assert c11.id == '1.1'
        c12 = comment(article)
        c12.add(req, '1')
        assert c12.id == '1.2'
        c21 = comment(article)
        c21.add(req, '2')
        assert c21.id == '2.1'
        c121 = comment(article)
        c121.add(req, '1.2')
        assert c121.id == '1.2.1'
        discussion = ArticleComment.list(req, article.id, Pager())
        cids = list(c.id for c in discussion)
        for it in (c1.id, c11.id, c12.id, c121.id, c2.id, c21.id):
            assert it in cids
    # enddef

    def test_mismatch_id(self, req):
        first = article(req)
        second = article(req, title=u'Ondřej Tůma')
        f1 = comment(first)
        f1.add(req)
        assert f1.id == '1'
        s1 = comment(second)
        s1.add(req)
        assert s1.id == '1'
        f2 = comment(first)
        f2.add(req)
        assert f2.id == '2'
        s2 = comment(second)
        s2.add(req)
        assert s2.id == '2'

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
    main(['-v', __file__])
