CREATE TABLE page (
    page_id integer not null primary key autoincrement,
    name text not null,
    title text not null default '',
    locale text not null default '',
    editor_rights text not null
);

CREATE unique index if not exists
    page_name_idx on page (name); 
