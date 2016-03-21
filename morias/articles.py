
from poorwsgi import app, state, redirect, SERVER_RETURN, send_json
from falias.sql import Sql
from falias.util import uni, ObjectEncoder

from random import randint

from core.login import check_login, check_referer, match_right, rights, \
    do_check_right, check_token, create_token
from core.render import generate_page
from core.lang import get_lang
# from core.errors import ErrorValue
from core.robot import robot_questions, RobotError

from lib.menu import Item
from lib.pager import Pager
from lib.articles import Article, FORMAT_RST, ArticleComment
from lib.rst import check_rst, rst2html

from user import user_sections
from admin import content_menu
from codebooks import build_class

_check_conf = (
    # morias common block
    ('morias', 'db', Sql),
    ('articles', 'in_menu',  bool, True),
    ('articles', 'is_root',  bool, False)
)

app.set_filter('tag', r'[\w\ ]+', uni)


def _call_conf(cfg, parser):
    if cfg.articles_in_menu:
        user_sections.append(Item('/articles', label="Articles"))
    if cfg.articles_is_root:
        app.set_route('/', articles_list_full)

right_editor = 'articles_editor'
right_author = 'articles_author'
module_rights = (right_editor, right_author)
rights.update(module_rights)

content_menu.append(Item('/admin/articles', label="Articles",
                         symbol="articles", rights=module_rights))


@app.route('/admin/articles')
def admin_articles(req):
    check_login(req)
    match_right(req, module_rights)

    show = req.args.getfirst('show', '', uni)

    pager = Pager(sort='desc')
    pager.bind(req.args)

    kwargs = {}

    if show == 'ready':
        pager.set_params(show=show)
        kwargs['state'] = 2
        kwargs['public_date'] = 0
    elif show == 'drafts':
        pager.set_params(show=show)
        kwargs['state'] = 1
    else:
        show = None

    if not do_check_right(req, right_editor):
        kwargs['author_id'] = req.login.id

    items = Article.list(req, pager, **kwargs)
    return generate_page(req, "admin/articles.html", pager=pager, items=items,
                         show=show)
# enddef


@app.route('/admin/articles/add', method=state.METHOD_GET_POST)
def admin_articles_add(req):
    check_login(req)
    match_right(req, module_rights)

    article = Article()
    if req.method == 'POST':
        article.bind(req.form, req.login.id)
        error = article.add(req)

        if error:
            return generate_page(req, "admin/articles_mod.html",
                                 article=article, error=error)

        redirect(req, '/admin/articles/%d' % article.id)
    # end

    article.state = 2 if do_check_right(req, right_editor) else 1
    return generate_page(req, "admin/articles_mod.html", article=article)
# enddef


@app.route('/admin/articles/<id:int>', state.METHOD_GET_POST)
def admin_articles_mod(req, id):
    check_login(req)
    match_right(req, module_rights)

    article = Article(id)
    if not article.get(req):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)
    if (not do_check_right(req, right_editor)
            and article.author_id != req.login.id):
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)

    Codebook = build_class('tags')
    pager = Pager(order='value', limit=-1)
    tags = Codebook.list(req, Codebook, pager)

    if req.method == 'POST':
        article.bind(req.form)
        error = article.mod(req)
        if error != article:
            return generate_page(req, "admin/articles_mod.html",
                                 article=article, error=error)

        if not article.get(req):
            raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    return generate_page(req, "admin/articles_mod.html", article=article,
                         token=create_token(req), tags=tags)
# enddef


@app.route('/admin/articles/rst', state.METHOD_POST)
def admin_articles_rst(req):
    check_login(req)
    match_right(req, module_rights)
    return check_rst(req)


@app.route('/admin/articles/<id:int>/disable', state.METHOD_POST)
@app.route('/admin/articles/<id:int>/enable', state.METHOD_POST)
def admin_articles_enable(req, id):
    check_login(req, '/log_in?referer=/admin/articles')
    match_right(req, module_rights)
    check_referer(req, '/admin/articles')

    article = Article(id)
    if not article.get(req):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    if (not do_check_right(req, right_editor)) \
            and (not (article.author_id == req.login.id
                 and article.public_date.year == 1970)):
        raise SERVER_RETURN(state.HTTP_FORBIDDEN)

    n_state = int(req.uri.endswith('/enable'))
    n_state = (n_state * 2) if article.public_date.year > 1970 else n_state
    article.set_state(req, n_state)

    redirect(req, '/admin/articles')
# enddef


@app.route('/admin/articles/<id:int>/tags', state.METHOD_GET)
def articles_tags(req, id):
    check_login(req)
    match_right(req, module_rights)
    return send_json(req, {'tags': Article.tags(req, id)}, cls=ObjectEncoder)


@app.route('/admin/articles/<id:int>/tags/<tag_id:int>/append',
           state.METHOD_POST)
def articles_append_tag(req, id, tag_id):
    check_login(req)
    match_right(req, module_rights)
    check_token(req, req.form.get('token'), uri='/admin/articles/%d' % id)

    article = Article(id)

    if not article.append_tag(req, tag_id):
        return send_json(req, {'reason': 'integrity_error'})
    req.content_type = 'application/json'
    return '{}'


@app.route('/admin/articles/<id:int>/tags/<tag_id:int>/remove',
           state.METHOD_POST)
def articles_remove_tag(req, id, tag_id):
    check_login(req)
    match_right(req, module_rights)
    check_token(req, req.form.get('token'), uri='/admin/articles/%d' % id)

    article = Article(id)
    article.remove_tag(req, tag_id)
    req.content_type = 'application/json'
    return '{}'


def articles_detail_internal(req, article, **kwargs):
    if article.format == FORMAT_RST:
        article.perex = rst2html(article.perex)
        article.body = rst2html(article.body)

    if article.data.get('discussion', True):
        discussion = ArticleComment.list(req, article.id, Pager(limit=-1))
    else:
        discussion = []

    qid = randint(0, len(robot_questions)-1)
    question, answer = robot_questions[qid]
    return generate_page(req, "articles_detail.html", article=article,
                         discussion=discussion,
                         question=question,  answer=answer, qid=hex(qid),
                         staticmenu=req.cfg.get_static_menu(req),
                         styles=('tiny-writer',), **kwargs)
# enddef


@app.route('/articles/<uri:word>')
@app.route('/articles/<id:int>')
def articles_detail(req, arg):
    id = arg if isinstance(arg, int) else None
    uri = arg if isinstance(arg, unicode) else None

    article = Article(id)
    article.uri = uri

    if uri and not article.get(req, key='uri'):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)
    if id and not article.get(req):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    return articles_detail_internal(req, article)
# enddef


def articles_comment_internal(req, uri=None, id=None):
    if not uri and not id:
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    article = Article(id)
    article.uri = uri
    if uri and not article.get(req, key='uri'):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)
    if id and not article.get(req):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)

    comment = ArticleComment()
    comment.bind(req.form, user_agent=req.user_agent, ip=req.remote_addr)

    robot = True if req.form.getfirst("robot", "", str) else False
    qid = int(req.form.getfirst("qid", '0', str), 16)
    question, answer = robot_questions[qid]
    check = req.form.getfirst("answer", "", str) == answer

    if robot or not check:
        rv = RobotError(comment=comment, check=check)
        return (article, rv)

    if req.login:
        comment.author_id = req.login.id
    rv = comment.add(req, parent=req.form.getfirst('parent', '', str))
    return (article, rv)
# enddef


@app.route('/articles/<uri:word>', method=state.METHOD_PUT)
@app.route('/articles/<id:int>', method=state.METHOD_PUT)
def articles_stats(req, arg):
    id = arg if isinstance(arg, int) else None
    uri = arg if isinstance(arg, unicode) else None

    article = Article(id)
    article.uri = uri
    if uri and not article.inc_data_key(req, key='uri', visits=1):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)
    if id and not article.inc_data_key(req, visits=1):
        raise SERVER_RETURN(state.HTTP_NOT_FOUND)
    return send_json(req, {'Ok': True})


@app.route('/articles/<uri:word>', method=state.METHOD_POST)
@app.route('/articles/<id:int>', method=state.METHOD_POST)
def articles_comment(req, arg):
    id = arg if isinstance(arg, int) else None
    uri = arg if isinstance(arg, unicode) else None

    article, rv = articles_comment_internal(req, uri, id)
    if hasattr(rv, 'reason'):
        return articles_detail_internal(req, article, error=rv, form=req.form)
    elif rv is None:
        raise SERVER_RETURN(state.HTTP_INTERNAL_SERVER_ERROR)
    redirect(req, '/articles/%s#comment_%s' % (article.uri, rv.id))


@app.route('/articles/<uri:word>/comment', method=state.METHOD_POST)
@app.route('/articles/<id:int>/comment', method=state.METHOD_POST)
def articles_comment_xhr(req, arg):
    id = arg if isinstance(arg, int) else None
    uri = arg if isinstance(arg, unicode) else None

    article, rv = articles_comment_internal(req, uri, id)
    # XXX: at now, isinstance not work, becouase, have another namespace
    # that rv....
    # if isinstance(rv, ErrorValue):
    if hasattr(rv, 'reason'):
        req.status = state.HTTP_BAD_REQUEST
        return send_json(req, rv, cls=ObjectEncoder)
    elif rv is None:
        req.status = state.HTTP_INTERNAL_SERVER_ERROR
        return send_json(req, {'reason': 'integrity_error'})

    return send_json(req, {'discussion': ArticleComment.list(req,
                           article.id, Pager(limit=-1)), 'last': rv.id},
                     cls=ObjectEncoder)
# enddef


@app.route('/articles')
@app.route('/<locale:word>/articles')
@app.route('/<locale:word>/articles/t/<tag:tag>')
def articles_list_full(req, locale=None, tag=None):
    pager = Pager(limit=5, sort='desc', order='create_date')
    pager.bind(req.args)

    kwargs = {'locale': (locale, '')} if locale else {}
    items = Article.list(req, pager, perex=True, public=1, tag=tag, **kwargs)

    lang = locale if locale else get_lang(req)
    return generate_page(req, "articles_list.html", pager=pager, items=items,
                         lang=lang, staticmenu=req.cfg.get_static_menu(req))
# enddef


@app.route('/articles/rss.xml')
def articles_rss(req):
    pager = Pager(limit=5, sort='desc', order='create_date')
    items = Article.list(req, pager, perex=True, public=1)
    return generate_page(req, "articles_rss.xml",
                         content_type="application/xml", pager=pager,
                         items=items, lang=get_lang(req),
                         webmaster=req.server_admin)


@app.route('/articles/t')
@app.route('/articles/tag')
def articles_tags_list(req):
    Codebook = build_class('tags')
    pager = Pager(order='value', limit=-1)
    tags = Codebook.list(req, Codebook, pager)
    return generate_page(req, "articles_tags.html", tags=tags)


@app.route('/articles/t/<tag:tag>')
@app.route('/articles/tag/<tag:tag>')
def articles_list(req, tag=None):
    return articles_list_full(req, tag=tag)
