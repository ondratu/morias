drop table if exists tags;

create table tags (
    tag_id integer not null primary key autoincrement,
    name text not null
);

create unique index if not exists
    tags_name_idx on tags (name);
