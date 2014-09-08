drop table if exists new;

CREATE TABLE new (
    new_id integer not null primary key autoincrement,
    enabled integer default 1,      -- new is enabled

    create_date integer not null,   -- unix timestamp in second from 1970-01-01
    title text not null,
    locale text not null,
    body text not null
);

CREATE index if not exists
    new_create_date_idx on new (create_date);
CREATE index if not exists
    new_enabled_idx on new (enabled);
