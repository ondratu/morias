drop table if exists articles_tags;
drop table if exists articles;

create table articles (
    article_id integer not null primary key autoincrement,
    uri text not null,
    serial_id integer default null references articles (article_id),
    author_id integer not null references logins (login_id), -- as author

    create_date integer not null,           -- unix timestamp in seconds from 1970-01-01
    public_date integer not null default 0, -- unix timestamp in seconds from 1970-01-01

    title text not null,
    locale text not null default '',
    perex text not null,
    body text not null,
    format integer not null default 1,      -- html (1), rst (2)

    state integer not null default 1,       -- disabled (0), new (1), ready (2)
    data text not null default '{}'         -- additional data (coments 0|1 etc)
);

create unique index if not exists
    articles_uri_idx on articles (uri);
create index if not exists
    articles_serial_id_idx on articles (serial_id);
create index if not exists
    articles_author_id_idx on articles (author_id);
create index if not exists
    articles_create_date_idx on articles (create_date);
create index if not exists
    articles_public_date_idx on articles (public_date);
create unique index if not exists
    articles_title_idx on articles (title);
create index if not exists
    articles_locale_idx on articles (locale);
create index if not exists
    articles_state_idx on articles (state);


create table articles_tags (
    article_id integer not null references articles (article_id),
    tag_id integer not null references tags (tag_id)
);

create index if not exists                  -- may be not need if unique exists
    articles_tags_article_id_idx on articles_tags (article_id);
create index if not exists                  -- may be not need if unique exists
    articles_tags_tag_id_idx on articles_tags (tag_id);
create unique index if not exists
    articles_tags_article_id_tag_id_idx on articles_tags (article_id, tag_id);
