drop table if exists redirects;

create table redirects (
    id integer not null primary key autoincrement,
    src text not null,
    dst text not null,
    code integer not null,
    state integer not null default 1 -- disabled (0), enabled (1)
);

create unique index if not exists
    redirects_src_idx on redirects (src);
