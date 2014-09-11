create table news_01 (
    new_id integer not null primary key autoincrement,
    author_id integer default null references logins (login_id),

    create_date integer not null,           -- unix timestamp in second from 1970-01-01
    public_date integer not null default 0, -- unix timestamp in seconds from 1970-01-01

    title text not null,
    locale text not null default '',
    body text not null,

    state integer not null default 1,       -- disable (0), draft (1), ready (2)
    data text not null default '{}'         -- additional data (coments 0|1 etc)
);

insert into news_01 (new_id, create_date, public_date, title, locale, body, state )
    select new_id, create_date, create_date, title, locale, body, enabled*2 from new;

drop table new;

alter table news_01 rename to news;
create index if not exists
    news_author_id_idx on news (author_id);
create index if not exists
    news_create_date_idx on news (create_date);
create index if not exists
    news_public_date_idx on news (public_date);
create index if not exists
    news_locale_idx on news (locale);
create index if not exists
    news_state_idx on news (state);

create table news_tags (
    new_id integer not null references news (new_id),
    tag_id integer not null references tags (tag_id)
);

create unique index if not exists
    news_tags_new_id_tag_id_idx on news_tags (new_id, tag_id);

