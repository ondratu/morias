drop table if exists articles_discussion;

create table articles_discussion (
    comment_id text not null,
    article_id integer not null references articles (article_id),

    author text not null,
    author_id integer default null references logins (login_id), -- as author

    create_date integer not null,           -- unix timestamp in seconds from 1970-01-01
    title text not null,
    body text not null,
    data text not null default '{}'         -- additional data (coments 0|1 etc)
);

create unique index if not exists
    articles_discussion_article_id_comment_id_idx
        on articles_discussion (article_id, comment_id);
