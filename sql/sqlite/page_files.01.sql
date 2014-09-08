create table page_files_01 (
    page_id integer not null primary key autoincrement,
    author_id integer default null references logins (login_id),
    name text not null,
    title text not null default '',
    locale text not null default '',
    editor_rights text not null default '[]'
);

insert into page_files_01 (page_id, name, title, locale, editor_rights)
    select page_id, name, title, locale, editor_rights from page;

drop table if exists page;

alter table page_files_01 rename to page_files;
create unique index if not exists
    page_files_name_idx on page_files (name);
