#!/usr/bin/env python

from falias.parser import Parser
from falias.sql import Sql

from argparse import ArgumentParser
from traceback import format_exc
from logging import error, info, basicConfig, INFO
from subprocess import Popen, PIPE
from os import path, remove, makedirs
from shutil import move, copyfile
from time import time, mktime
from json import dumps
from hashlib import md5
from mimetypes import guess_extension

from morias.lib.articles import Article


INSTALL_DB = path.abspath(
    path.join(path.dirname(__file__), 'sql/sqlite/install.sh'))


def to_dots(tree_id):
    """tree_id = '1122112'"""
    pos = 0
    while pos < len(tree_id):
        l = tree_id[pos]
        tree_id = tree_id[:pos] + '.' + tree_id[pos+1:]
        pos = pos+int(l, 16)+1
    return tree_id.strip('.')


def webname(id, _md5, mime_type):
        hex_id = "%06x" % id
        return "%s/%s_%s%s" % (hex_id[:-3], hex_id, _md5[:6],
                               guess_extension(mime_type) or '')


class Config(Parser):

    def __init__(self, config):
        Parser.__init__(self)
        self.read(config)

        self.dst_db = self.get('main', 'dst_db', cls=Sql)
        self.src_db = self.get('main', 'src_db', cls=Sql)

        self.dst_attach_path = self.get('main', 'dst_attachments_path')
        self.src_attach_path = self.get('main', 'src_attachments_path')

        self.dst_page_path = self.get('main', 'dst_page_path')


class Worker(object):

    def __init__(self, config):
        self.dst_db = config.dst_db
        self.src_db = config.src_db
        self.dst_attach_path = config.dst_attach_path
        self.src_attach_path = config.src_attach_path
        self.dst_page_path = config.dst_page_path

    def prepare_db(self, backup=True):
        if path.isfile(self.dst_db.dbfile):
            if backup:
                move(self.dst_db.dbfile,
                     "%s.bak_%s" % (self.dst_db.dbfile, time()))
            else:
                remove(self.dst_db.dbfile)
        print(INSTALL_DB)
        pp = Popen([INSTALL_DB, self.dst_db.dbfile], stdout=PIPE, stdin=PIPE,
                   close_fds=True)
        pp.stdin.close()
        print(pp.stdout.read())
        pp.wait()
        pp.stdout.close()

    def users(self):
        self.users = {}
        print("Migrating users:")
        with self.dst_db.transaction() as dst_cur:
            with self.src_db.transaction() as src_cur:
                src_cur.execute("""
                    SELECT user_id, rights, email, first_name, last_name
                    FROM tb_morias_login""")
                for row in src_cur:
                    user_id, rights, email, first_name, last_name = row
                    if not email:
                        continue
                    name = '%s %s' % (first_name, last_name)
                    enabled = 1 if 'L' not in rights else 0
                    rights = ['super'] if 'A' in rights else ['user']
                    dst_cur.execute("""
                        INSERT INTO logins
                            (email, name, rights, enabled, passwd)
                            VALUES (%s, %s, %s, %d, '')
                        """, (email, name.strip(), dumps(rights), enabled))
                    self.users[user_id] = dst_cur.lastrowid
                    print("\t%s" % email)
    # enddef

    def tags(self):
        self.tags = {}
        print("Migrating tags:")
        with self.dst_db.transaction() as dst_cur:
            with self.src_db.transaction() as src_cur:
                src_cur.execute("SELECT tag_tree, name FROM tb_morias_tag")
                for row in src_cur:
                    tag_tree, name = row
                    dst_cur.execute("INSERT INTO tags (name) VALUES (%s)",
                                    name)
                    self.tags[tag_tree] = dst_cur.lastrowid
                    print("\t%s" % name)
                    # redirects
                    src = "/a/old_tag/%s" % tag_tree
                    dst = "/a/t/%s" % name
                    dst_cur.execute("""
                       INSERT INTO redirects (src, dst, code, state)
                           VALUES (%s, %s, 301, 1)
                       """, (src, dst))
                    print("\t%s -> %s" % (src, dst))
        self.categories = {}
        print("Migrating categories to tags:")
        with self.dst_db.transaction() as dst_cur:
            with self.src_db.transaction() as src_cur:
                src_cur.execute(
                    "SELECT tree_id, name FROM tb_morias_category")
                for row in src_cur:
                    tree_id, name = row
                    dst_cur.execute("INSERT INTO tags (name) VALUES (%s)",
                                    name)
                    self.categories[tree_id] = dst_cur.lastrowid
                    print("\t%s" % name)
    # enddef

    def articles(self):
        self.articles = {}
        print("Migrating articles:")
        with self.dst_db.transaction(logger=info) as dst_cur:
            with self.src_db.transaction(logger=info) as src_cur:
                src = "/clanek/(?P<uri>\w+)$"
                dst = '/a/{0}'
                dst_cur.execute("""
                    INSERT INTO redirects (src, dst, code, state)
                        VALUES (%s, %s, 301, 1)
                    """, (src, dst))
                print("\t%s -> %s" % (src, dst))
                src = "/rss_articles.rss"
                dst = '/articles/rss.xml'
                dst_cur.execute("""
                    INSERT INTO redirects (src, dst, code, state)
                        VALUES (%s, %s, 301, 1)
                    """, (src, dst))
                print("\t%s -> %s" % (src, dst))

                src_cur.execute("""
                    SELECT article_id, user_id, category_tree, l.shortcut,
                        create_date, public, forum, title, seo_url, formating,
                        home_text, body_text, counter, rating_count,
                        rating_value
                    FROM tb_morias_article AS a
                        LEFT JOIN tb_falias_language AS l
                            ON (l.lang_id = a.lang_id)
                    ORDER BY article_id
                    """)
                for row in src_cur:
                    article_id, user_id, category_tree, shortcut, create_date, \
                        public, forum, title, seo_url, formating, home_text, \
                        body_text, counter, rating_count, rating_value = row

                    author_id = self.users[user_id]
                    uri = Article.make_uri(title)
                    create_date = int(mktime(create_date.timetuple()))
                    public_date = create_date if public else 0
                    formating = 2 if formating == 'wiki' else 1
                    data = {'visits': counter,
                            'rating_count': rating_count,
                            'rating_value': rating_value,
                            'discussion': bool(forum)}

                    dst_cur.execute("""
                        INSERT INTO articles
                                (uri, author_id, create_date, public_date,
                                 title, locale, perex, body, format, state,
                                 data)
                            VALUES (%s, %d, %d, %d, %s, %s, %s, %s, %d, 2, %s)
                        """, (uri, author_id, create_date, public_date,
                              title, shortcut, home_text, body_text, formating,
                              dumps(data)))
                    article_new_id = dst_cur.lastrowid
                    dst_cur.execute("""
                        INSERT INTO articles_tags (article_id, tag_id)
                            VALUES (%d, %d)
                        """, (article_new_id, self.categories[category_tree]))
                    self.articles[article_id] = (article_new_id, author_id)
                    print("\t%s" % title)
                    if seo_url != uri:
                        src = "/clanek/%s" % seo_url
                        dst = "/a/%s" % uri
                        dst_cur.execute("""
                            INSERT INTO redirects (src, dst, code, state)
                                VALUES (%s, %s, 301, 1)
                            """, (src, dst))
                        print("\t%s \n\t-> %s" % (src, dst))
    # enddef

    def articles_tags(self):
        print("Migrating articles tags:")
        with self.dst_db.transaction(logger=info) as dst_cur:
            with self.src_db.transaction(logger=info) as src_cur:
                src_cur.execute("""
                    SELECT article_id, tag_tree
                        FROM tb_morias_article_tag ORDER BY article_id
                    """)
                for row in src_cur:
                    dst_cur.execute("""
                        INSERT INTO articles_tags
                            (article_id, tag_id) VALUES (%d, %d)
                        """, (self.articles[row[0]][0], self.tags[row[1]]))
            print("\t%d" % src_cur.rowcount)

    def articles_discussions(self):
        print("Migrating articles discussions:")
        states = {'deleted': 0, 'ready': 1, 'vulgar': 2, 'censored': 3}

        with self.dst_db.transaction(logger=info) as dst_cur:
            with self.src_db.transaction(logger=info) as src_cur:
                src_cur.execute("""
                    SELECT state, user_id, tree_id, a_name, date, name, text,
                        article_id
                    FROM tb_morias_forum_data AS f
                        JOIN tb_morias_article_forum AS a
                            ON (f.forum_id = a.forum_id)
                    ORDER BY date
                """)

                for row in src_cur:
                    state, user_id, tree_id, a_name, date, name, text, \
                        article_id = row
                    author_id = self.users.get(user_id, None)
                    article_id = self.articles[article_id][0]
                    create_date = int(mktime(date.timetuple()))

                    dst_cur.execute("""
                        INSERT INTO articles_discussion
                                (comment_id, article_id, state, author,
                                 author_id, create_date, title, body)
                            VALUES (%s, %d, %d, %s, %s, %d, %s, %s)
                        """, (to_dots(tree_id), article_id, states[state],
                              a_name, author_id, create_date, name, text))
                    print("\t%s" % name)

    def articles_attachments(self):
        print("Migrating articles attachments:")
        self.files_uri = {}
        self.article_files = {}

        with self.dst_db.transaction(logger=info) as dst_cur:
            with self.src_db.transaction(logger=info) as src_cur:
                src_cur.execute("""
                    SELECT file_id, article_id, name, mime_type, note,
                        upload_date
                    FROM tb_morias_article_file
                    ORDER BY file_id
                """)

                for row in src_cur:
                    file_id, article_id, name, mime_type, note, \
                        upload_date = row
                    timestamp = int(mktime(upload_date.timetuple()))
                    _md5 = md5(str(time()+timestamp)+name).hexdigest()
                    data = {'description': note}
                    uploader_id = self.articles[article_id][1]

                    dst_cur.execute("""
                        INSERT INTO attachments (uploader_id, timestamp,
                                mime_type, file_name, md5, data)
                            VALUES (%d, %d, %s, %s, %s, %s
                        )""", (uploader_id, timestamp, mime_type, name, _md5,
                               dumps(data)))
                    attach_id = dst_cur.lastrowid
                    dst_cur.execute("""
                        INSERT INTO object_attachments (attachment_id,
                                object_type, object_id)
                            VALUES (%d, 'article', %d)
                        """, (attach_id, self.articles[article_id][0]))
                    # save
                    web_uri = webname(attach_id, _md5, mime_type)
                    dst_path = self.dst_attach_path + '/' + web_uri
                    if not path.exists(path.dirname(dst_path)):
                        makedirs(path.dirname(dst_path))
                    src_path = "%s/morias_article/%d/files/%s" % \
                        (self.src_attach_path, article_id, name)
                    copyfile(src_path, dst_path)

                    old_uri = "data/morias_article/%d/files/%s" % \
                        (article_id, name)
                    new_uri = "/attachments/%s" % web_uri

                    # update uri in articles
                    dst_cur.execute("""
                        SELECT perex, body FROM articles
                        WHERE article_id = %d
                    """, self.articles[article_id][0])
                    perex, body = dst_cur.fetchone()
                    dst_cur.execute("""
                        UPDATE articles SET perex=%s, body=%s
                        WHERE article_id = %d
                    """, (perex.replace(old_uri, new_uri),
                          body.replace(old_uri, new_uri),
                          self.articles[article_id][0]))

                    print("\t%s" % name)

            print("-> need to regenerate thumbs after install")

    def pages(self):
        self.pages = {}
        formatings = {'xhtml': (1, 'html'), 'self': (2, 'rst')}
        if not path.exists(self.dst_page_path):
            makedirs(self.dst_page_path)
        print("Migrating pages:")
        with self.dst_db.transaction(logger=info) as dst_cur:
            with self.src_db.transaction(logger=info) as src_cur:
                src_cur.execute("""
                    SELECT text_id, user_id, l.shortcut, t.name, formating,
                        text
                    FROM tb_morias_text AS t
                        LEFT JOIN tb_falias_language AS l
                            ON (l.lang_id = t.lang_id)
                    ORDER BY text_id
                    """)
                for row in src_cur:
                    text_id, user_id, shortcut, name, formating, text = row
                    file_name = "%s_%s.%s" % (Article.make_uri(name),
                                              shortcut.lower(),
                                              formatings[formating][1])
                    dst_cur.execute("""
                        INSERT INTO page_files (author_id, name, title, locale,
                                format)
                            VALUES (%s, %s, %s, %s, %d)
                    """, (self.users.get(user_id, None),
                          file_name, name, shortcut, formatings[formating][0]))
                    page_id = dst_cur.lastrowid

                    dst_path = self.dst_page_path + '/' + file_name
                    with open(dst_path, 'w+') as src:
                        src.write(text.encode('utf-8'))
                    self.pages[text_id] = (page_id,
                                           self.users.get(user_id, None))
                    print("\t%s (%s)" % (name, file_name))
        print("-> need to regenerate outputs if not dynamics are set")

    def pages_attachements(self):
        print("Migrating pages attachments:")
        self.files_uri = {}
        self.pages_files = {}

        with self.dst_db.transaction(logger=info) as dst_cur:
            with self.src_db.transaction(logger=info) as src_cur:
                src_cur.execute("""
                    SELECT file_id, text_id, name, mime_type, note,
                        upload_date
                    FROM tb_morias_text_file
                    ORDER BY file_id
                """)

                for row in src_cur:
                    file_id, text_id, name, mime_type, note, \
                        upload_date = row
                    timestamp = int(mktime(upload_date.timetuple()))
                    _md5 = md5(str(time()+timestamp)+name).hexdigest()
                    data = {'description': note}
                    uploader_id = self.pages[text_id][1]

                    dst_cur.execute("""
                        INSERT INTO attachments (uploader_id, timestamp,
                                mime_type, file_name, md5, data)
                            VALUES (%d, %d, %s, %s, %s, %s
                        )""", (uploader_id, timestamp, mime_type, name, _md5,
                               dumps(data)))
                    attach_id = dst_cur.lastrowid
                    dst_cur.execute("""
                        INSERT INTO object_attachments (attachment_id,
                                object_type, object_id)
                            VALUES (%d, 'page_file', %d)
                        """, (attach_id, self.pages[text_id][0]))
                    # save
                    web_uri = webname(attach_id, _md5, mime_type)
                    dst_path = self.dst_attach_path + '/' + web_uri
                    if not path.exists(path.dirname(dst_path)):
                        makedirs(path.dirname(dst_path))
                    src_path = "%s/morias_text/%d/files/%s" % \
                        (self.src_attach_path, text_id, name)
                    copyfile(src_path, dst_path)

                    old_uri = "data/morias_text/%d/files/%s" % \
                        (text_id, name)
                    new_uri = "/attachments/%s" % web_uri

                    # update uri in pages
                    dst_cur.execute("""
                        SELECT name FROM page_files
                        WHERE page_id = %d
                    """, self.pages[text_id][0])
                    file_name = dst_cur.fetchone()[0]
                    dst_path = self.dst_page_path + '/' + file_name
                    with open(dst_path, 'r') as page:
                        content = page.read().decode('utf-8')
                    with open(dst_path, 'w+') as page:
                        content = content.replace(old_uri, new_uri)
                        page.write(content.encode('utf-8'))

                    print("\t%s" % name)

            print("-> need to regenerate thumbs after install")

    def page_menu(self):
        pass    # only one link...

    def run(self):
        self.prepare_db(False)
        self.users()
        self.tags()
        self.articles()
        self.articles_tags()
        self.articles_discussions()
        self.articles_attachments()
        self.pages()
        self.pages_attachements()
        self.page_menu()
# endclass


if __name__ == "__main__":
    parser = ArgumentParser(
        description=__doc__,
        usage="%(prog)s [options]")
    parser.add_argument(
        "-c", "--config", type=str, default='migration.ini',
        metavar="<file>", help="Path to config file.")
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="verbose mode")

    args = parser.parse_args()
    if args.verbose:
        basicConfig(level=INFO)
    try:
        config = Config(args.config)

        worker = Worker(config)
        worker.run()
    except BaseException as e:
        error(str(args))
        error(format_exc())
        parser.error('%s' % repr(e))
        exit(1)
    else:
        exit(0)
# endif
